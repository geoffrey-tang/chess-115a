#include "move_gen.h"

// IMPLEMENT EDGE CHECKING

Bitboard king_move(uint8_t square){
    Bitboard b = 1ULL << square;
    Bitboard temp = 0;
    for(int i : {1, 7, 8, 9}){
        temp = ((1ULL << square) << i) | ((1ULL << square) >> i);
        b |= temp;
    }
    return b ^ (1ULL << square);
}

Bitboard knight_move(uint8_t square){
    Bitboard b = 1ULL << square;
    Bitboard temp = 0;
    for(int i : {6, 10, 15, 17}){
        temp = ((1ULL << square) << i) | ((1ULL << square) >> i);
        b |= temp;
    }
    return b ^ (1ULL << square);
}