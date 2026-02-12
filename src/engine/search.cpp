#include <limits>
#include "search.h"
#include "board.h"
#include "move_gen.h"
#include "constants.h"
#include "eval.h"
#include "uci.h"

void init_state_stack(Board& board, StateStack& ss){
    ss.ply = 0;
    ss.states[0] = board.root;
    ss.states[0].previous = nullptr;
    board.st = &ss.states[0];
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
    init_state_stack(b, ss);
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

SearchResult search_root(Board &b, int depth){
    SearchResult result;
    result.best_move = 0;
    result.score_cp = 0;

    StateStack ss;
    init_state_stack(b, ss);

    int best_score = -1 * std::numeric_limits<int>::max();
    std::vector<Move> moves = generate_moves(b, ss);
    Move best_move = moves[0];

    if(moves.empty()){
        result.best_move = 0;
        result.score_cp = 0;
        return result;
    }

    for(Move m : moves) {
        do_move(b, ss, m);

        int score = -alpha_beta_negamax(-std::numeric_limits<int>::max(), std::numeric_limits<int>::max(), b, ss, depth - 1);
        if(score > best_score){
            best_score = score;
            best_move = m;
        }
        undo_move(b, ss, m);
    }
    result.best_move = best_move;
    result.score_cp = best_score;
    return result;
}

int alpha_beta_negamax(int alpha, int beta, Board& b, StateStack& ss, int depth){
    if(depth == 0) return b.to_move == WHITE ? material_score(b) : -material_score(b); // change this to eval when proper eval is implemented
    int best = -std::numeric_limits<int>::max();
    std::vector<Move> moves = generate_moves(b, ss);

    // check/stale mate check
    if(moves.empty()){
        uint8_t color = b.to_move;
        bool in_check = square_attacked(b, king_square(b, color), !color);
        if(in_check)
            return -10000 + ss.ply; // this is to prioritize faster mates
        else
            return 0;
    }

    for(Move m : moves){
        do_move(b, ss, m);
        int score = -alpha_beta_negamax(-beta, -alpha, b, ss, depth - 1); 
        undo_move(b, ss, m);
        if(score > best){
            best = score;
            // alpha is the lower bound; the best score we can force, so we can ignore anything worse than alpha
            // here we simply update alpha to represent the best score we can get
            if(score > alpha) alpha = score; 
        } 
        // beta is the higher bound; the worst score (for us) they can force, so if we find something better (for us), the opponent can fall back on beta so we ignore this line
        // here we cut off based on beta; if this line results in a better score than beta, then we know that the opponent will not allow this and playing this is just hope chess
        if(score >= beta) return score; 
    }
    return best;
}