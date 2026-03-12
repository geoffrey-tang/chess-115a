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
// Vector of pseudolegal moves
std::vector<Move> generate_pseudo(Board& board, uint8_t color);

// Vector of legal moves
std::vector<Move> generate_moves(Board& board, StateStack& ss);

// Vector of legal captures
std::vector<Move> generate_captures(Board& board, StateStack& ss);

// Make/unmake moves
void do_move(Board& board, StateStack& ss, Move move);

void undo_move(Board& board, StateStack& ss, Move move);

// Utilities
// Get the square that a certain color's king is on, assuming only 1 king
uint8_t king_square(Board& board, uint8_t color);

// Check if a square is attacked by a certain color
bool square_attacked(Board& board, int sq, uint8_t by_color);

// Update castling rights after a move. st assumes that the Board's current BoardState has already been updated, so only use after a move is done
void update_castling(Board& board, uint8_t color, uint8_t moved_piece, Move move, BoardState& st); // color = color of the moving piece

// Checks for legality
bool legal(Board& board, StateStack& ss, Move move);

// Checks if the destination square is a valid destination and returns a bitboard of the destination square
Bitboard check_dst(int square, int offset);

// Checks if a move is a capture
bool is_capture(Board& b, Move m);

// Gets the index of the first non-zero bit
int lsb(Bitboard b);

// Gets the first non-zero square on a bitboard, then pops the bit from the bitboard
uint8_t pop_lsb(Bitboard& b);

// Returns number of non-zero bits
int popcount(Bitboard bb);