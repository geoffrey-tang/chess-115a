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
    // Perft test cases: https://www.chessprogramming.org/Perft_Results
    // starting pos: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
    // pos 2: r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1
    // pos 3: 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1
    // pos 4: r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1
    // pos 5: rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8
    // pos 6: r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10
    Board board = get_board(fen);
    print_board(board);
    std::cout << "FEN: " << fen << "\n";

    std::cout << "Material score (centipawns, +white / -black): "
              << material_score(board) << "\n";

    StateStack ss;
    init_state_stack(board, ss);
    int target_depth = 5;
    for(int depth = 1; depth <= target_depth; depth++){
        std::cout << "Depth " << depth << ": " << perft(board, ss, depth) << std::endl;
    }
    std::cout << std::endl;
    perft_divide(board, target_depth); // compare to stockfish's perft

    //return run_uci_loop();
    return 0;
}
