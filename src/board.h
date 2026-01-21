#include <iostream>
#include <cstdint>
#include <string>
#include <vector>
#include <array>
#include <bitset>

#define LAST_BIT 63


using Piece = int;
using Bitboard = uint64_t;

constexpr Bitboard file_a = 0x8080808080808080ULL;
constexpr Bitboard file_b = file_a >> 1;
constexpr Bitboard file_c = file_a >> 2;
constexpr Bitboard file_d = file_a >> 3;
constexpr Bitboard file_e = file_a >> 4;
constexpr Bitboard file_f = file_a >> 5;
constexpr Bitboard file_g = file_a >> 6;
constexpr Bitboard file_h = file_a >> 7;

constexpr Bitboard rank_1 = 0xFF;
constexpr Bitboard rank_2 = rank_1 << (8 * 1);
constexpr Bitboard rank_3 = rank_1 << (8 * 2);
constexpr Bitboard rank_4 = rank_1 << (8 * 3);
constexpr Bitboard rank_5 = rank_1 << (8 * 4);
constexpr Bitboard rank_6 = rank_1 << (8 * 5);
constexpr Bitboard rank_7 = rank_1 << (8 * 6);
constexpr Bitboard rank_8 = rank_1 << (8 * 7);

enum Pieces : uint8_t{
    PAWN,
    KNIGHT,
    BISHOP,
    ROOK,
    QUEEN,
    KING,
    NONE
};

enum Colors : uint8_t{
    WHITE,
    BLACK
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