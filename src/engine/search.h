#pragma once

#include "board.h"
#include "move_gen.h"
#include "constants.h"

void init_state_stack(Board& board, StateStack& ss);

uint64_t perft(Board& b, StateStack& ss, int depth);

uint64_t perft_divide(Board& b, int depth);