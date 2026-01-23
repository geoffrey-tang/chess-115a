#pragma once

#include "board.h"

Bitboard king_move(uint8_t square, Board& board, uint8_t color); // get king moves from a specific square

Bitboard knight_move(uint8_t square, Board& board, uint8_t color); // get knight moves from a specific square

Bitboard bishop_move(uint8_t square, Board& board, uint8_t color); 

Bitboard rook_move(uint8_t square, Board& board, uint8_t color); 

Bitboard queen_move(uint8_t square, Board& board, uint8_t color); 

Bitboard pawn_move(uint8_t square, Board& board, uint8_t color);

Bitboard check_dst(uint8_t square, int offset);

//Bitboard rook_mask(uint8_t square);