#include <iostream>
#include <cstdint>
#include <string>
#include <vector>
#include <array>
#include <bitset>

#define LAST_BIT 63


using Piece = int;
using Bitboard = uint64_t;

struct Pieces {
    static constexpr Piece PAWN = 0;
    static constexpr Piece KNIGHT = 1;
    static constexpr Piece BISHOP = 2;
    static constexpr Piece ROOK = 3;
    static constexpr Piece QUEEN = 4;
    static constexpr Piece KING = 5;
    static constexpr Piece NONE = 6;
};

struct Board { // Representation: a8, b8, c8, ..., h8, a7, b7, c7, ..., a1, b1, ..., h8
    std::array<std::array<Bitboard, 6>, 2> bb_pieces{};
    std::array<Bitboard, 2> bb_colors{};
};

// print a specific bitboard
void print_bitboard(Bitboard bitboard);

// print the board state in a human readable fashion
void print_board(Board bitboards);

// parse a FEN string into its 6 constituent parts
std::vector<std::string> fen_parse(std::string fen);

// using the piece list component of a FEN string, generate bitboards and put them into a provided array
// only use with first parsed component of FEN string, not the full string
void generate_bb_from_fen_pieces(std::string fen_pieces, Board& bb_pieces);

uint64_t get_mask(int rank, int file);