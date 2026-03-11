#pragma once
#include "board.h"
#include "constants.h"
#include "move_gen.h"

// initialize piece square lookup tables
void init_pst();

// aggregate evaluation + means white is better, - means black is better
int evaluate(const Board& b);

int game_phase(const Board& b);

int delta_piece_value(int piece, int phase);