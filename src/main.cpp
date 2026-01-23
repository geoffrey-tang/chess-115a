#include <iostream>
#include <cstdint>
#include <string>
#include <vector>
#include <bitset>
#include "board.h"
#include "move_gen.h"

int main(int argc, char* argv[]){
    std::string fen = "r1bqkbnr/ppp1pppp/n7/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3"; 
    //starting pos: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
    //en passant: r1bqkbnr/ppp1pppp/n7/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3
    //random pos: 5r2/1p4pp/6k1/P2p4/4n1P1/1P3P1P/3R1K2/8 w - - 1 35
    Board bitboard;

    std::vector<std::string> fen_tokens = fen_parse(fen);
    get_bb_from_fen_pieces(fen_tokens[0], bitboard);
    get_turn_from_fen(fen_tokens[1], bitboard);
    get_castle_from_fen(fen_tokens[2], bitboard);
    get_en_passant_from_fen(fen_tokens[3], bitboard);

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
    
    return 0;
}