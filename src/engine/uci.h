#pragma once
#include <string>
#include "board.h"
#include "move_gen.h"
#include "constants.h"
#include "search.h"

struct Board;

struct Game{
    Board board;
    StateStack ss;
};

int run_uci_loop();

std::string move_to_uci(Move m);

Move uci_to_move(Board& b, StateStack& ss, std::string uci);

