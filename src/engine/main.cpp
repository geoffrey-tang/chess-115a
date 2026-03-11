#include <iostream>
#include <cstdint>
#include <string>
#include <vector>
#include <bitset>
#include <chrono>
#include "board.h"
#include "move_gen.h"
#include "uci.h"
#include "constants.h"
#include "eval.h"
#include "search.h"
#include "zobrist.h"

int main(void){
    Zobrist::init();
    init_pst();
    return run_uci_loop();
}
