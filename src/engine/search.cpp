#include <limits>
#include <algorithm>
#include "search.h"
#include "board.h"
#include "move_gen.h"
#include "constants.h"
#include "eval.h"
#include "uci.h"

constexpr int MATE = 20000;
constexpr int MATE_BAND = 1000; // safe range that means mate
constexpr int ASPIRATION_WINDOW = 30;

// check if score is within mate range
inline bool is_mate_score(int s) {
    return std::abs(s) >= (MATE - MATE_BAND);
}

// convert a score at current ply to a ply independent score
inline int score_to_tt(int s, int ply) {
    if (!is_mate_score(s)) return s;
    // If s is +mate, make it slightly smaller as ply increases; if -mate, slightly larger
    return (s > 0) ? (s + ply) : (s - ply);
}

// convert a stored TT score back to the current ply’s perspective
inline int score_from_tt(int s, int ply) {
    if (!is_mate_score(s)) return s;
    return (s > 0) ? (s - ply) : (s + ply);
}

BoardState* init_state_stack(Board& board, StateStack& ss){
    ss.ply = 0;
    ss.states[0] = board.root;
    ss.states[0].previous = nullptr;
    return &ss.states[0];
}

uint64_t perft(Board& b, StateStack& ss, int depth){
    if(depth == 0) return 1;
    uint64_t nodes = 0;
    std::vector<Move> moves = generate_moves(b, ss);

    for(Move m : moves){
        do_move(b, ss, m);
        nodes += perft(b, ss, depth - 1);
        undo_move(b, ss, m);
    }
    return nodes;
}

uint64_t perft_divide(Board& b, int depth){
    StateStack ss;
    BoardState* new_st = init_state_stack(b, ss);
    StGuard guard(b, new_st);
    uint64_t total = 0;
    std::vector<Move> moves = generate_moves(b, ss);
    
    std::cout << "perft_divide at depth " << depth << std::endl;
    for (Move m : moves) {
        do_move(b, ss, m);
        uint64_t nodes = perft(b, ss, depth - 1);
        undo_move(b, ss, m);

        std::cout << move_to_uci(m) << ": " << nodes << "\n";
        total += nodes;
    }

    std::cout << "\nNodes searched: " << total << "\n";
    return total;
}

SearchResult iter_deepening(Board& b, TranspositionTable& tt, SearchStats& stats, int max_depth){
    tt.new_search();
    SearchHeuristic sh;
    SearchResult pv_move; // principal variation
    pv_move.best_move = 0;
    pv_move.score_cp = 0;

    int prev_score = 0; // start centered at 0 cp
    int base_window = ASPIRATION_WINDOW; // in centipawns

    for(int depth = 1; depth <= max_depth; depth++){
        int alpha = -32000;
        int beta  =  32000;
        int current_window = base_window;

        if (depth >= 2) {
            alpha = prev_score - current_window;
            beta  = prev_score + current_window;
        }

        while(true){
            SearchResult r = search_root_window(alpha, beta, b, tt, sh, stats, depth, pv_move.best_move);
            // fail-low: score <= alpha, too optimistic
            if (r.score_cp <= alpha) {
                current_window *= 2;
                alpha = -32000;
                beta  = prev_score + current_window;
                continue;
            }

            // fail-high: score >= beta, too pessimistic
            if (r.score_cp >= beta) {
                current_window *= 2;
                beta  = 32000;
                alpha = prev_score - current_window;
                continue;
            }

            // success
            pv_move = r;
            prev_score = pv_move.score_cp;
            break;
        }
        if(pv_move.score_cp > 10000) break; // end search early if forced mate
    }
    return pv_move;
}

SearchResult search_root_window(int alpha, int beta, Board& b, TranspositionTable& tt, SearchHeuristic& sh, SearchStats& stats, int depth, Move prev_best){
    SearchResult result;
    result.best_move = 0;
    result.score_cp = 0;

    StateStack ss;
    BoardState* new_st = init_state_stack(b, ss);
    StGuard guard(b, new_st);

    uint64_t key = b.st->zobrist;
    Move tt_move = 0;
    int tt_score = 0;

    // check transposition tables and tighten window accordingly
    int alpha_probe = alpha, beta_probe = beta;
    if (tt.probe(key, depth, alpha_probe, beta_probe, tt_score, tt_move)) {
        // Root cutoff / exact hit
        result.best_move = tt_move;
        result.score_cp = score_from_tt(tt_score, ss.ply);
        return result;
    }
    alpha = alpha_probe; beta = beta_probe;

    // movegen
    std::vector<Move> moves = generate_moves(b, ss);
    if(moves.empty()){
        result.best_move = 0;
        result.score_cp = 0;
        return result;
    }

    // sort moves in order: pv, tt_move, captures, killer 1, killer 2, all other quiet moves in order on history
    move_to_index(moves, prev_best, 0);
    size_t start = 1;
    if (tt_move && tt_move != prev_best && moves.size() > 1) {
        move_to_index(moves, tt_move, 1);
        start = 2;
    }
    if (moves.size() > start) {
        std::sort(moves.begin() + start, moves.end(), [&](Move amove, Move bmove) {
                return score_move(b, ss, sh, amove) > score_move(b, ss, sh, bmove);
            }
        );
    }

    // main search loop
    int best_score = -std::numeric_limits<int>::max();
    Move best_move = moves[0];
    int entry_alpha = alpha;
    for(Move m : moves) {
        do_move(b, ss, m);
        int score = -alpha_beta_negamax(-beta, -alpha, b, ss, tt, sh, stats, depth - 1);
        undo_move(b, ss, m);
        if(score > best_score){
            best_score = score;
            best_move = m;
        }
        if(score > alpha) alpha = score;
        if (score >= beta) {
            tt.store(key, depth, score_to_tt(score, ss.ply), TT_LOWERBOUND, m);
            result.best_move = m;
            result.score_cp  = score;
            return result;
        }
    }
    TTFlag flag = TT_EXACT;
    if (best_score <= entry_alpha) flag = TT_UPPERBOUND; // fail-low vs entry window

    tt.store(key, depth, score_to_tt(best_score, ss.ply), flag, best_move);
    result.best_move = best_move;
    result.score_cp = best_score;
    return result;
}

int alpha_beta_negamax(int alpha, int beta, Board& b, StateStack& ss, TranspositionTable& tt, SearchHeuristic& sh, SearchStats& stats, int depth){
    stats.nodes++;
    if (ss.ply > stats.seldepth) stats.seldepth = ss.ply;
    uint64_t key = b.st->zobrist;
    Move tt_move = 0;
    int tt_score = 0;

    // check the transposititon table and tighten window accordingly
    int alpha_probe = alpha, beta_probe = beta;
    if (tt.probe(key, depth, alpha_probe, beta_probe, tt_score, tt_move)) {
        return score_from_tt(tt_score, ss.ply);
    }
    alpha = alpha_probe;
    beta = beta_probe;

    // check for finish
    if(depth == 0) return quiesce(alpha, beta, b, ss, stats);
    std::vector<Move> moves = generate_moves(b, ss);

    // check/stale mate check
    if(moves.empty()){
        uint8_t color = b.to_move;
        bool in_check = square_attacked(b, king_square(b, color), !color);
        if(in_check)
            return -MATE + ss.ply;
        else
            return 0;
    }

    // sort moves in order: tt_move, captures, killer 1, killer 2, all other quiet moves based on history
    move_to_index(moves, tt_move, 0);
    size_t start = (tt_move && !moves.empty()) ? 1 : 0;
    
    if(moves.size() > start){    
        std::sort(moves.begin() + start, moves.end(), [&](Move amove, Move bmove) {
                return score_move(b, ss, sh, amove) > score_move(b, ss, sh, bmove);
            }
        );
    }

    // main search loop
    int best = -std::numeric_limits<int>::max();
    Move best_move = 0;
    int entry_alpha = alpha;
    for(Move m : moves){
        do_move(b, ss, m);
        int score = -alpha_beta_negamax(-beta, -alpha, b, ss, tt, sh, stats, depth - 1); 
        undo_move(b, ss, m);
        if(score > best){
            best = score;
            best_move = m;
        } 
        // alpha is the lower bound; the best score we can force, so we can ignore anything worse than alpha
        // here we simply update alpha to represent the best score we can get
        if(score > alpha) alpha = score; 

        // beta is the higher bound; the worst score (for us) they can force, so if we find something better (for us), the opponent can fall back on beta so we ignore this line
        // here we cut off based on beta; if this line results in a better score than beta, then we know that the opponent will not allow this and playing this is just hope chess
        if(score >= beta) { 
            if (!is_capture(b, m)) { // quiet beta cutoff = update heuristics
                sh.update_killer(m, ss.ply);
                sh.update_history(m, b.to_move, depth * depth);
            }
            tt.store(key, depth, score_to_tt(score, ss.ply), TT_LOWERBOUND, m);
            return score;
        } 
    }
    TTFlag flag = TT_EXACT;
    if (best <= entry_alpha) flag = TT_UPPERBOUND;
    tt.store(key, depth, score_to_tt(best, ss.ply), flag, best_move);
    return best;
}


int quiesce(int alpha, int beta, Board& b, StateStack& ss, SearchStats& stats){
    stats.nodes++;
    if (ss.ply > stats.seldepth) stats.seldepth = ss.ply;
    int static_eval = b.to_move == WHITE ? evaluate(b) : -evaluate(b);
    int best = static_eval;
    if(best >= beta) return best;
    if(best > alpha) alpha = best;

    std::vector<Move> captures = generate_captures(b, ss);
    std::sort(captures.begin(), captures.end(), [&](Move amove, Move bmove) {
                return mvv_lva_score(b, amove) > mvv_lva_score(b, bmove);
            }
        );
    for(Move m : captures){
        do_move(b, ss, m);
        int score = -quiesce(-beta, -alpha, b, ss, stats);
        undo_move(b, ss, m);

        if(score >= beta) return score;
        if(score > best) best = score;
        if(score > alpha) alpha = score;
    }

    return best;
}

void move_to_index(std::vector<Move>& moves, Move m, size_t idx){
    if(m == 0 || idx >= moves.size()) return;
    auto it = std::find(moves.begin()+idx, moves.end(), m);
    if(it != moves.end())
        std::iter_swap(moves.begin()+idx, it);
}

int score_move(Board& b, StateStack& ss, SearchHeuristic& sh, Move m){
    if(is_capture(b, m)) return ((MAX_HISTORY * 3) + mvv_lva_score(b, m));

    if (ss.ply >= 0 && ss.ply < MAX_PLY) {
        if (m == sh.killers[ss.ply][0]) return (MAX_HISTORY * 2);
        if (m == sh.killers[ss.ply][1]) return ((MAX_HISTORY * 2) - 1);
    }

    return sh.history[b.to_move][get_from_sq(m)][get_to_sq(m)]; // clamped to MAX_HISTORY
    // score order should be: PV move, TT move, captures, killer 1, killer 2, all other quiet moves in order of history score
    // PV and TT moves will be handled during search
}

int mvv_lva_score(Board& b, Move m) {
    int from = get_from_sq(m);

    int attacker = piece_on_square(b, b.to_move, from);
    int victim = get_captured_piece(b, m);

    if (attacker == NONE || victim == NONE) return 0;

    // Bigger victim is better, smaller attacker is better
    return 10 * MVV_LVA_PIECE_VALUE[victim] - MVV_LVA_PIECE_VALUE[attacker];
}

