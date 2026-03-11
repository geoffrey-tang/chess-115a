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

struct SearchLimits{
    int depth = MAX_PLY - 1;
    int movetime = -1;
    int wtime = -1;
    int btime = -1;
    int winc = 0;
    int binc = 0;
    bool infinite = false;
};

int run_uci_loop();

std::string move_to_uci(Move m);

Move uci_to_move(Board& b, StateStack& ss, std::string uci);

