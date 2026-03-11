#pragma once

#include <algorithm>
#include <atomic>

#include "board.h"
#include "move_gen.h"
#include "constants.h"
#include "time_man.h"

extern bool stop;

static constexpr int MVV_LVA_PIECE_VALUE[6] = {
    100, // pawn
    300, // knight
    300, // bishop
    500, // rook
    900, // queen
    0    // king
};

struct SearchResult {
    Move best_move;
    int score_cp; // score in centipawns, perspective = side to move (negamax)
};

struct SearchStats {
    int nodes = 0;
    int depth = 0;
    int seldepth = 0;
};

struct SearchHeuristic {
    Move killers[MAX_PLY][2]{};
    int history[2][64][64]{}; // [color][from][to]

    void clear(){
        for (int ply = 0; ply < MAX_PLY; ++ply) {
            killers[ply][0] = 0;
            killers[ply][1] = 0;
        }

        for (int c = 0; c < 2; ++c)
            for (int from = 0; from < 64; ++from)
                for (int to = 0; to < 64; ++to)
                    history[c][from][to] = 0;
    }

    void update_killer(Move m, int ply){
        if (ply < 0 || ply >= MAX_PLY || m == 0) return;
        if (killers[ply][0] == m) return; // already best killer
        killers[ply][1] = killers[ply][0];
        killers[ply][0] = m;
    }

    void update_history(Move m, int color, int bonus){
        int from = get_from_sq(m);
        int to = get_to_sq(m);
        int clamped_bonus = std::clamp(bonus, -MAX_HISTORY, MAX_HISTORY);
        history[color][from][to] += clamped_bonus - history[color][from][to] * abs(clamped_bonus) / MAX_HISTORY;
    }
};

struct TTEntry {
    uint16_t key16 = 0;    // 16-bit verification
    int16_t  score = 0;    
    int8_t   depth = -1;   // searched depth
    uint8_t  flag = TT_EMPTY;
    Move move = 0;
    uint8_t  age = 0;
};

struct TranspositionTable {
    std::vector<TTEntry> table;
    size_t mask = 0; 
    uint8_t age = 0;

    static uint16_t key16(uint64_t key) { return uint16_t(key >> 48); } // Grab the first 16 bits from a hash to use as verification

    // Resize table to a specified MB and round down to the closest power of 2
    void resize_mb(size_t megabytes) {
        const size_t bytes = megabytes * 1024ull * 1024ull;
        size_t entries = bytes / sizeof(TTEntry);
        if (entries < 2) entries = 2;

        // largest power-of-two <= entries
        size_t n = 1;
        while ((n << 1) <= entries) n <<= 1;

        table.clear();
        table.resize(n);
        mask = n - 1;
        age = 0;
    }

    void new_search() { ++age; } // Call at the start of each new root search

    void clear() { // Fill table with empty entries
        std::fill(table.begin(), table.end(), TTEntry{});
        age = 0;
    }

    bool probe(uint64_t key, int depth, int& alpha, int& beta, int& out_score, Move& out_move) {
        if (table.empty()) return false;
        TTEntry& entry = table[key & mask];
        if (entry.flag == TT_EMPTY) return false;
        if (entry.key16 != TranspositionTable::key16(key)) return false;

        out_move = entry.move;
        
        if(entry.depth >= depth){
            int s = entry.score;
            if (entry.flag == TT_EXACT){ 
                out_score = s; 
                return true; 
            }
            if (entry.flag == TT_LOWERBOUND) {
                if(s >= beta){
                    out_score = s; 
                    return true; // beta cutoff
                }
                else if(s > alpha) alpha = std::max(alpha, s);
            }

            if (entry.flag == TT_UPPERBOUND) {
                if (s <= alpha){
                    out_score = s; 
                    return true; // alpha cutoff
                }
                else if(s < beta) beta = std::min(beta, s);
            }
        }
        return false;
    }

    // Store an entry
    // Replacement policy: replace if empty, different key, older age, or shallower depth.
    void store(uint64_t key, int depth, int score, TTFlag flag, Move bestMove) {
        if(table.empty()) return;
        TTEntry& e = table[key & mask];
        const uint16_t k16 = key16(key);

        const bool same = (e.flag != TT_EMPTY && e.key16 == k16);
        const bool replace =
            (e.flag == TT_EMPTY) ||
            (!same) ||
            (e.age != age) ||
            (depth >= e.depth);

        if (!replace) return;

        e.key16  = k16;
        e.depth  = (int8_t)std::clamp(depth, -128, 127);
        e.score  = (int16_t)std::clamp(score, -32000, 32000);
        e.flag   = (uint8_t)flag;
        e.move   = bestMove;
        e.age    = age;
    }
};

// Initializes a stack of BoardStates to use for search
BoardState* init_state_stack(Board& board, StateStack& ss);

// Perft debugging functions, prints number of leaf nodes at a certain depth
uint64_t perft(Board& b, StateStack& ss, int depth);

uint64_t perft_divide(Board& b, int depth);

// Main iterative deepening function
SearchResult iter_deepening(Board& b, TranspositionTable& tt, SearchStats& stats, TimeManager& tm, int max_depth);

// Main search function, returns the best move
SearchResult search_root_window(int alpha, int beta, Board& b, TranspositionTable& tt, SearchHeuristic& sh, SearchStats& stats, TimeManager& tm, int depth, Move prev_best = 0);

// Negamax search through the entire search tree up to depth; implement alpha-beta pruning
int alpha_beta_negamax(int alpha, int beta, Board& b, StateStack& ss, TranspositionTable& tt, SearchHeuristic& sh, SearchStats& stats, TimeManager& tm, int depth);

// Quiescence search to continue searching through captures, alleviating horizon effect
int quiesce(int alpha, int beta, Board& b, StateStack& ss, SearchStats& stats, TimeManager& tm);

// Puts a move to the front of a vector of Moves, enabling better move ordering
void move_to_index(std::vector<Move>& moves, Move m, size_t idx);

int score_move(Board& b, StateStack& ss, SearchHeuristic& sh, Move m);

int mvv_lva_score(Board& b, Move m);
