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

int main(void){
    init();
    std::string fen = "rnbq1rk1/pp3ppp/2p2n2/4N3/1bBP1B2/2N5/PPP3PP/R2Q1RK1 b - - 0 1"; 
    //starting pos: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
    //king + rooks starting pos: r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1
    //white blocked O-O: 4k3/8/8/8/8/8/8/R3KB1R w KQ - 0 1
    //white blocked O-O-O: 4k3/8/8/8/8/8/8/RN2K2R w KQ - 0 1
    //sample pos - vienna gambit: rnbq1rk1/pp3ppp/2p2n2/4N3/1bBP1B2/2N5/PPP3PP/R2Q1RK1 b - - 0 1
    Board bitboard = get_board(fen);
    print_board(bitboard);
    std::cout << "FEN: " << fen << "\n";

    std::cout << "Material score (centipawns, +white / -black): "
              << material_score(bitboard) << "\n";

    std::vector<Move> movelist = generate_moves(bitboard, bitboard.to_move);
    std::cout << "PSEUDO-LEGAL MOVES:\n";
    for(Move i : movelist){
        std::cout << int_to_algebraic(get_from_sq(i)) << int_to_algebraic(get_to_sq(i)) << "\n";
    }
    //return run_uci_loop();
    return 0;
}
