#pragma once

#include <iostream>
#include <cstdint>
#include <string>
#include <vector>
#include <array>
#include <bitset>
#include <ctype.h>
#include "constants.h"

static constexpr int MAX_PLY = 512;

// Board state info that will be used in the search stack
struct BoardState {
    uint8_t castle = 0;
    uint8_t en_passant = 64;
    int halfmove = 0;
    int fullmove = 1;
    uint8_t captured_piece = NONE;   // Pieces or NONE
    uint8_t captured_square = 64;  // where the captured piece was removed/restored
    BoardState* previous = nullptr;
};

// Current board position; we separate BoardState in order to avoid having to use excessive memory storing bitboards + time copying bitboards
struct Board {
    std::array<std::array<Bitboard, 6>, 2> bb_pieces{};
    std::array<Bitboard, 2> bb_colors{};
    uint8_t to_move;
    BoardState root;
    BoardState* st = nullptr;
};

// Stack used for searching
struct StateStack {
    std::array<BoardState, MAX_PLY> states;
    int ply = 0;
};

// Initializing constants & lookup tables (not done)
void init();

// Print a single bitboard in an 8x8 grid
void print_bitboard(Bitboard bitboard);

// Print a full Board position, along with state info
void print_board(Board board);

// Generate and print the legal movelist for the given Board
void print_moves(Board& board, StateStack& ss);

// Parse a FEN string into its 6 constituent parts
std::vector<std::string> fen_parse(std::string fen);

// Helper functions for board generation from fen
void get_bb_from_fen_pieces(std::string fen_pieces, Board& bb_pieces);

void get_turn_from_fen(std::string fen_turn, Board& bitboards);

void get_castle_from_fen(std::string fen_castle, Board& bitboards);

void get_en_passant_from_fen(std::string fen_passant, Board& bitboards);

void get_moves_from_fen(std::string fen_halfmove, std::string fen_fullmove, Board& bitboards);

// Generates a Board from a FEN string, and set search tree root
Board get_board(std::string fen);


// Square utilities
// Converts from internal uint8_t square representation to algebraic notation
std::string int_to_algebraic(uint8_t sq);

// Converts from algebraic notation to internal uint8_t square representation 
uint8_t algebraic_to_int(std::string algebraic);

// Generates a bitboaord mask from rank and file
uint64_t get_mask(int rank, int file);

// Returns file of a given square (0-7)
uint8_t get_file(uint8_t square);

// Returns rank of a given square (0-7)
uint8_t get_rank(uint8_t square);


// Move type utilities
// Create a Move (uint16_t) using src square, dst square, and any flags.
Move set_move(uint8_t from, uint8_t to, uint16_t flags, uint8_t promo_piece = NONE);

// Get src square from a Move
uint8_t get_from_sq(Move move);

// Get dst square from a Move
uint8_t get_to_sq(Move move);

// Get promotion piece from a Move
uint8_t get_promo(Move move);

// Get a Move's flags
uint8_t get_move_flags(Move move);

// Returns the promotion piece of a Move
uint8_t parse_promotion_flag(Move move);


// Board utilities
// Check if a square is empty
bool empty_square(uint8_t square, Board& board);

// Get the piece that is on a square
uint8_t piece_on_square(Board& board, uint8_t color, uint8_t sq);

// Prints all bitboards of a Board
void debug_bb(Board& board);
