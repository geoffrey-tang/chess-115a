#pragma once
#include "board.h"

int material_score(const Board& b);

// aggregate evaluation + means white is better, - means black is better
int evaluate(const Board& b);