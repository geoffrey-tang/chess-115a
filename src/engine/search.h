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

// Main search function, returns the best move
Move search(Board &b, int depth);

// Negamax search through the entire search tree up to depth; implement alpha-beta pruning
int alpha_beta_negamax(int alpha, int beta, Board& b, StateStack& ss, int depth);