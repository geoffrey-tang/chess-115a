#include <iostream>
#include <cstdint>
#include <string>
#include <vector>
#include <bitset>
#include "board.h"
#include "move_gen.h"

int main(void){
    std::string fen = "5r2/1p4pp/6k1/P2p4/4n1P1/1P3P1P/3R1K2/8 b - - 1 35"; 
    //starting pos: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
    //en passant: r1bqkbnr/ppp1pppp/n7/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3
    //random pos: 5r2/1p4pp/6k1/P2p4/4n1P1/1P3P1P/3R1K2/8 w - - 1 35
    Board bitboard = get_board(fen);
    print_board(bitboard);
    std::cout << "FEN: " << fen << "\n";

    std::vector<Move> movelist = generate_moves(bitboard, bitboard.to_move);
    std::cout << "PSEUDO-LEGAL MOVES:\n";
    for(Move i : movelist){
        std::cout << int_to_algebraic(get_from_sq(i)) << int_to_algebraic(get_to_sq(i)) << "\n";
    }

    return 0;
}