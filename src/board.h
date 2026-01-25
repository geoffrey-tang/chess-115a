#pragma once

#include <iostream>
#include <cstdint>
#include <string>
#include <vector>
#include <array>
#include <bitset>
#include <ctype.h>
#include "constants.h"

struct Board {
    std::array<std::array<Bitboard, 6>, 2> bb_pieces{};
    std::array<Bitboard, 2> bb_colors{};
    uint8_t to_move;
    uint8_t castle = 0;
    uint8_t en_passant;
    int halfmove;
    int fullmove;
};

// print a specific bitboard
void print_bitboard(Bitboard bitboard);

// print the board state in a human readable fashion
void print_board(Board bitboards);

// parse a FEN string into its 6 constituent parts
std::vector<std::string> fen_parse(std::string fen);

// helper functions for board generation from fen
void get_bb_from_fen_pieces(std::string fen_pieces, Board& bb_pieces);

void get_turn_from_fen(std::string fen_turn, Board& bitboards);

void get_castle_from_fen(std::string fen_castle, Board& bitboards);

void get_en_passant_from_fen(std::string fen_passant, Board& bitboards);

void get_moves_from_fen(std::string fen_halfmove, std::string fen_fullmove, Board& bitboards);

Board get_board(std::string fen);

// util
uint8_t algebraic_to_int(std::string algebraic);

std::string int_to_algebraic(uint8_t integer);

uint64_t get_mask(int rank, int file);

uint8_t get_file(uint8_t square);

uint8_t get_rank(uint8_t square);

Move set_move(uint8_t from, uint8_t to);

uint8_t get_from_sq(Move move);

uint8_t get_to_sq(Move move);

uint8_t empty_square(uint8_t square, Board& board);

void debug_bb(Board& board);
