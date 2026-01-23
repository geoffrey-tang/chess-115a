#include "move_gen.h"
#include "board.h"

Bitboard king_move(uint8_t square){ // make more elegant later
    Bitboard b = 1ULL << square;
    Bitboard attacks = 0;

    attacks |= (b >> 8) | (b << 8); //S, N
    attacks |= (b & ~file_a_bb) << 1; //W
    attacks |= (b & ~file_a_bb) >> 7; //SW
    attacks |= (b & ~file_a_bb) << 9; //NW
    attacks |= (b & ~file_h_bb) >> 1; //E
    attacks |= (b & ~file_h_bb) << 7; //NE
    attacks |= (b & ~file_h_bb) >> 9; //SE

    return attacks;
}

Bitboard knight_move(uint8_t square){
    Bitboard b = 1ULL << square;
    Bitboard attacks = 0;

    // 2 north
    attacks |= (b & ~file_a_bb) << 17; // W
    attacks |= (b & ~file_h_bb) << 15; // E

    // 2 south
    attacks |= (b & ~file_a_bb) >> 15; // W
    attacks |= (b & ~file_h_bb) >> 17; // E

    // 2 west
    attacks |= (b & ~(file_a_bb | file_b_bb)) << 10; // N
    attacks |= (b & ~(file_a_bb | file_b_bb)) >> 6; // S

    // 2 east
    attacks |= (b & ~(file_g_bb | file_h_bb)) >> 10; // S
    attacks |= (b & ~(file_g_bb | file_h_bb)) << 6; // N

    return attacks;
}