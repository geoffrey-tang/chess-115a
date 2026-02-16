#pragma once

#include "board.h"
#include "move_gen.h"
#include "constants.h"

struct SearchResult {
    Move best_move;
    int score_cp; // score in centipawns, perspective = side to move (negamax)
};

// Initializes a stack of BoardStates to use for search
void init_state_stack(Board& board, StateStack& ss);

// Perft debugging functions, prints number of leaf nodes at a certain depth
uint64_t perft(Board& b, StateStack& ss, int depth);

uint64_t perft_divide(Board& b, int depth);

// Main iterative deepening function
SearchResult iter_deepening(Board b, int max_depth);

// Main search function, returns the best move
SearchResult search_root(Board& b, int depth, Move prev_best = 0);

// Negamax search through the entire search tree up to depth; implement alpha-beta pruning
int alpha_beta_negamax(int alpha, int beta, Board& b, StateStack& ss, int depth);

// Quiescence search to continue searching through captures, alleviating horizon effect
int quiesce(int alpha, int beta, Board& b, StateStack& ss);

// Puts a move to the front of a vector of Moves, enabling better move ordering
void put_move_first(std::vector<Move>& moves, Move m);