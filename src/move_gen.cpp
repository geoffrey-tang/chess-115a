#include <cmath>
#include "move_gen.h"
#include "board.h"

Bitboard king_move(uint8_t square, Board& board, uint8_t color){
    Bitboard b = 0;
    for(int i : {-9, -8, -7, -1, 1, 7, 8, 9}){
        b |= check_dst(square, i);
    }
    return b & ~board.bb_colors[color];
    /*
    attacks |= (b << 8) | (b >> 8); //S, N
    attacks |= (b & ~file_a_bb) >> 1; //W
    attacks |= (b & ~file_a_bb) << 7; //NW
    attacks |= (b & ~file_a_bb) >> 9; //SW
    attacks |= (b & ~file_h_bb) << 1; //E
    attacks |= (b & ~file_h_bb) >> 7; //SE
    attacks |= (b & ~file_h_bb) << 9; //NE

    return attacks & ~board.bb_colors[color];
    */
}

Bitboard knight_move(uint8_t square, Board& board, uint8_t color){
    Bitboard b = 0;
    for(int i : {-17, -15, -10, -6, 6, 10, 15, 17}){
        b |= check_dst(square, i);
    }
    return b & ~board.bb_colors[color];
    /*
    // 2 north
    attacks |= (b & ~file_a_bb) << 17; // E
    attacks |= (b & ~file_h_bb) << 15; // W

    // 2 south
    attacks |= (b & ~file_a_bb) >> 15; // E
    attacks |= (b & ~file_h_bb) >> 17; // W

    // 2 east
    attacks |= (b & ~(file_g_bb | file_h_bb)) << 10; // N
    attacks |= (b & ~(file_g_bb | file_h_bb)) >> 6; // S

    // 2 west
    attacks |= (b & ~(file_a_bb | file_b_bb)) >> 10; // S
    attacks |= (b & ~(file_a_bb | file_b_bb)) << 6; // N

    return attacks & ~board.bb_colors[color];
    */
}

Bitboard bishop_move(uint8_t square, Board& board, uint8_t color){
    Bitboard b = 0;
    for(int i : {-9, -7, 7, 9}){
        uint8_t s = square;
        while(check_dst(s, i)){
            b |= (1ULL << (s += i));
            if((board.bb_colors[0] | board.bb_colors[1]) & (1ULL << s)){
                break;
            }
        }
    }
    return b & ~board.bb_colors[color];
}

Bitboard rook_move(uint8_t square, Board& board, uint8_t color){
    Bitboard b = 0;
    for(int i : {-8, -1, 1, 8}){
        uint8_t s = square;
        while(check_dst(s, i)){
            b |= (1ULL << (s += i));
            if((board.bb_colors[0] | board.bb_colors[1]) & (1ULL << s)){
                break;
            }
        }
    }
    return b & ~board.bb_colors[color];
}

Bitboard queen_move(uint8_t square, Board& board, uint8_t color){
    return bishop_move(square, board, color) | rook_move(square, board, color);
}

Bitboard check_dst(uint8_t square, int offset){
    uint8_t dst = square + offset;
    if(A1 <= dst && dst <= H8){
        return abs(int(get_file(square)) - int(get_file(dst))) <= 2 ? (1ULL << dst) : 0ULL;
    }
    else{
        return 0ULL;
    }
}

Bitboard pawn_move(uint8_t square, Board& board, uint8_t color){
    Bitboard empty = ~(board.bb_colors[0] | board.bb_colors[1]);
    Bitboard pawn_attacks = color == WHITE ? 
        (((1ULL << (square + 9)) & ~file_a_bb) | ((1ULL << (square + 7)) & ~file_h_bb)) & board.bb_colors[BLACK] :
        (((1ULL << (square - 9)) & ~file_h_bb) | ((1ULL << (square - 7)) & ~file_a_bb)) & board.bb_colors[WHITE];
    Bitboard single_push = color == WHITE ? 
        ((1ULL << (square + 8)) & empty) :
        ((1ULL << (square - 8)) & empty);
    Bitboard double_push = color == WHITE ? 
        (single_push << 8) & empty & rank_4_bb :
        (single_push >> 8) & empty & rank_5_bb;
    return pawn_attacks | single_push | double_push;
}

/* might use this for magic bitboards later;
Bitboard rook_mask(uint8_t square){
    return (((file_a_bb << get_file(square)) | (rank_1_bb << (8 * get_rank(square)))) ^ (1ULL << square)) & ~rook_mask_file & ~rook_mask_rank;
}
*/