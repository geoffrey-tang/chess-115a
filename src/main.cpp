#include <iostream>
#include <cstdint>
#include <string>
#include <vector>
#include <bitset>
#include "board.h"
#include "move_gen.h"

int main(int argc, char* argv[]){
    std::string fen = "5r2/1p4pp/6k1/P2p4/4n1P1/1P3P1P/3R1K2/8 w - - 1 35"; //starting pos: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
    Board bitboard;

    std::vector<std::string> fen_tokens = fen_parse(fen);
    generate_bb_from_fen_pieces(fen_tokens[0], bitboard);

    std::string pieces[12] = {"w_pawn", "w_bishop", "w_knight", "w_rook", "w_queen", "w_king", 
        "b_pawn", "b_bishop", "b_knight", "b_rook", "b_queen", "b_king"};
    std::string colors[2] = {"white", "black"};

    std::cout << "Starting bitboards:\n\n";
    for(int color = 0; color < 2; color++){
        for(int piece = 0; piece < 6; piece++){
            std::cout << pieces[(color * 2) + piece] << "\n";
            print_bitboard(bitboard.bb_pieces[color][piece]);
            std::cout << "------------------------\n";
        }
    }
    for(int color = 0; color < 2; color++){
        std::cout << colors[color] << "\n";
        print_bitboard(bitboard.bb_colors[color]);
        std::cout << "------------------------\n";
    }
    std::cout << "all" << "\n";
    print_bitboard(bitboard.bb_colors[0] | bitboard.bb_colors[1]);
    std::cout << "------------------------\n";

    print_board(bitboard);
    std::cout << "\nFEN: " << fen << "\n";

    print_bitboard(1ULL << E4);
    std::cout << "\n";
    print_bitboard(king_move(D4));
    std::cout << "\n";
    print_bitboard(knight_move(D4));
    std::cout << "\n";
    return 0;
}