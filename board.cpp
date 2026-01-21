#include <iostream>
#include <cstdint>
#include <string>
#include <vector>
#include <bitset>
#include "board.h"

int main(){
    std::string fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"; //starting pos: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
    uint64_t bitboards[12] = { 0 };
    /*
    Representation: a8, b8, c8, ..., h8, a7, b7, c7, ..., a1, b1, ..., h8
    0 = white pawn
    1 = white bishop
    2 = white knight
    3 = white rook
    4 = white queen
    5 = white king
    6 = black pawn
    7 = black bishop
    8 = black knight
    9 = black rook
    10 = black queen
    11 = black king
    */
    std::vector<std::string> fen_tokens = fen_parse(fen);
    generate_bb_fen_pieces(fen_tokens[0], bitboards);

    std::string pieces[12] = {"w_pawn", "w_bishop", "w_knight", "w_rook", "w_queen", "w_king", 
        "b_pawn", "b_bishop", "b_knight", "b_rook", "b_queen", "b_king"};
    std::cout << "Starting bitboards:\n\n";
    for(int i = 0; i < 12; i++){
        std::cout << pieces[i] << "\n";
        print_bitboard(bitboards[i]);
        std::cout << "------------------------\n";
    }
    print_board(bitboards);
    std::cout << "\nFEN: " << fen << "\n";
    return 0;
}