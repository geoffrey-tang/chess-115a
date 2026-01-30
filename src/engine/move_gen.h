#pragma once

#include "board.h"
#include "constants.h"

Bitboard king_move(uint8_t square); // get king moves from a specific square

Bitboard knight_move(uint8_t square); // get knight moves from a specific square

Bitboard bishop_move(uint8_t square, Bitboard occupancy); // initial assumption is that all occupied squares are enemies; AND w/ ~board.bb_colors[color] to exclude allies

Bitboard rook_move(uint8_t square, Bitboard occupancy); 

Bitboard queen_move(uint8_t square, Bitboard occupancy); 

Bitboard pawn_move(uint8_t square, Board& board, uint8_t color);

bool square_attacked(Board& board, int sq, uint8_t by_color);

std::vector<Move> generate_moves(Board& board, uint8_t color); // currently generates 1 big list; change later for alpha beta pruning

Bitboard check_dst(uint8_t square, int offset);

int lsb(Bitboard b);

uint8_t pop_lsb(Bitboard& b);

//Bitboard rook_mask(uint8_t square);