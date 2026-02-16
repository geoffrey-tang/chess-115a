#pragma once
#include "board.h"
#include "constants.h"
#include "move_gen.h"

// initialize piece square lookup tables
void init_pst();

// aggregate evaluation + means white is better, - means black is better
int evaluate(const Board& b);