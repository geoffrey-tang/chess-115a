#pragma once
#include "board.h"
#include "constants.h"
#include "move_gen.h"

// Initialize piece square lookup tables
void init_pst();

// Aggregate evaluation; + means white is better, - means black is better
int evaluate(const Board& b);

// Returns game phase; lower means endgame, higher means midgame
int game_phase(const Board& b);

// Returns a piece value with game phase interpolation for delta pruning
int delta_piece_value(int piece, int phase);