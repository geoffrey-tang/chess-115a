#pragma once

#include "board.h"
#include "constants.h"

// Attack bitboard generation
// All but pawn_move assume no friendlies, so you must explicitly exclude allies with (& ~board.bb_colors[color])
Bitboard king_move(uint8_t square);

Bitboard knight_move(uint8_t square);

Bitboard bishop_move(uint8_t square, Bitboard occupancy); 

Bitboard rook_move(uint8_t square, Bitboard occupancy); 

Bitboard queen_move(uint8_t square, Bitboard occupancy); 

Bitboard pawn_move(uint8_t square, Board& board, uint8_t color);

// Move generation
std::vector<Move> generate_pseudo(Board& board, uint8_t color); // currently generates 1 big list; change later for alpha beta pruning

std::vector<Move> generate_moves(Board& board, StateStack& ss);

std::vector<Move> generate_captures(Board& board, StateStack& ss);

// Make/unmake moves
void do_move(Board& board, StateStack& ss, Move move);

void undo_move(Board& board, StateStack& ss, Move move);

// Utilities
uint8_t king_square(Board& board, uint8_t color);

bool square_attacked(Board& board, int sq, uint8_t by_color);

void update_castling(Board& board, uint8_t color, uint8_t moved_piece, Move move, BoardState& st); // color = color of the moving piece

bool legal(Board& board, StateStack& ss, Move move);

Bitboard check_dst(int square, int offset);

bool is_capture(Board& b, Move m);

int lsb(Bitboard b);

uint8_t pop_lsb(Bitboard& b);

int popcount(Bitboard bb);

//Bitboard rook_mask(uint8_t square);