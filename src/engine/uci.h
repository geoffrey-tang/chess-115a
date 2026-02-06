#pragma once
#include <string>
#include "board.h"
#include "move_gen.h"
#include "constants.h"
#include "search.h"

struct Board;

int run_uci_loop();

std::string move_to_uci(Move m);

