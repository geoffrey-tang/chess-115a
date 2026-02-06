#include <iostream>
#include <cstdint>
#include <string>
#include <vector>
#include <bitset>
#include "board.h"
#include "move_gen.h"
#include "uci.h"
#include "constants.h"
#include "eval.h"
#include "search.h"

int main(void){
    init();
    std::string fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"; 
    //starting pos: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
    //king + rooks starting pos: r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1
    //white blocked O-O: 4k3/8/8/8/8/8/8/R3KB1R w KQ - 0 1
    //white blocked O-O-O: 4k3/8/8/8/8/8/8/RN2K2R w KQ - 0 1
    //rights set but rook missing: 4k3/8/8/8/8/8/8/4K2R w KQ - 0 1
    //en passant: 4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1
    //promotion (white): 1n2k3/P7/8/8/8/8/8/4K3 w - - 0 1
    //promotion (black): 4k3/8/8/8/8/8/7p/6N1K b - - 0 1
    //sample pos - vienna gambit: rnbq1rk1/pp3ppp/2p2n2/4N3/1bBP1B2/2N5/PPP3PP/R2Q1RK1 b - - 0 1
    Board bitboard = get_board(fen);
    print_board(bitboard);
    std::cout << "FEN: " << fen << "\n";

    std::cout << "Material score (centipawns, +white / -black): "
              << material_score(bitboard) << "\n";

    StateStack ss;
    init_state_stack(bitboard, ss);
    for(int i = 1; i <= 5; i++){
        std::cout << "Depth " << i << ": " << perft(bitboard, ss, i) << std::endl;
    }

    //return run_uci_loop();
    return 0;
}
