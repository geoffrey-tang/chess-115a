#pragma once

#include <cstdint>

#define LAST_BIT 63

using Bitboard = uint64_t;
using Move = uint16_t;

constexpr Bitboard file_a_bb = 0x0101010101010101ULL;
constexpr Bitboard file_b_bb = file_a_bb << 1;
constexpr Bitboard file_c_bb = file_a_bb << 2;
constexpr Bitboard file_d_bb = file_a_bb << 3;
constexpr Bitboard file_e_bb = file_a_bb << 4;
constexpr Bitboard file_f_bb = file_a_bb << 5;
constexpr Bitboard file_g_bb = file_a_bb << 6;
constexpr Bitboard file_h_bb = file_a_bb << 7;

constexpr Bitboard rank_1_bb = 0xFF;
constexpr Bitboard rank_2_bb = rank_1_bb << (8 * 1);
constexpr Bitboard rank_3_bb = rank_1_bb << (8 * 2);
constexpr Bitboard rank_4_bb = rank_1_bb << (8 * 3);
constexpr Bitboard rank_5_bb = rank_1_bb << (8 * 4);
constexpr Bitboard rank_6_bb = rank_1_bb << (8 * 5);
constexpr Bitboard rank_7_bb = rank_1_bb << (8 * 6);
constexpr Bitboard rank_8_bb = rank_1_bb << (8 * 7);

// gets the edge squares of a file/rank for rook relevant occupancy
constexpr Bitboard rook_mask_file = 0x0100000000000001ULL;
constexpr Bitboard rook_mask_rank = 0x81;

extern Bitboard line_bb[64][64]; // lookup table for the line (from edge to edge) on which 2 squares are (both orthogonally and diagonally)
extern Bitboard between_bb[64][64]; // lookup table for the line (from square to square) on which 2 squares are (both orthogonally an diagonally)
extern Bitboard ray_bb[64][64]; // lookup table for the line (from square to edge) on which 2 squares are (both orthogonally an diagonally)
extern Bitboard castle_path[4];

enum Squares : uint8_t { // from LSB to MSB
    A1, B1, C1, D1, E1, F1, G1, H1,
    A2, B2, C2, D2, E2, F2, G2, H2,
    A3, B3, C3, D3, E3, F3, G3, H3,
    A4, B4, C4, D4, E4, F4, G4, H4,
    A5, B5, C5, D5, E5, F5, G5, H5,
    A6, B6, C6, D6, E6, F6, G6, H6,
    A7, B7, C7, D7, E7, F7, G7, H7,
    A8, B8, C8, D8, E8, F8, G8, H8,
};

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

enum Files : uint8_t{
    FILE_A,
    FILE_B,
    FILE_C,
    FILE_D,
    FILE_E,
    FILE_F,
    FILE_G,
    FILE_H
};

enum Ranks : uint8_t{
    RANK_1,
    RANK_2,
    RANK_3,
    RANK_4,
    RANK_5,
    RANK_6,
    RANK_7,
    RANK_8
};

enum Castling : uint8_t{
    NO_CASTLE,
    WHITE_OO,
    WHITE_OOO = WHITE_OO << 1,
    BLACK_OO = WHITE_OO << 2,
    BLACK_OOO = WHITE_OO << 3,
    OO = WHITE_OO | BLACK_OO,
    OOO = WHITE_OOO | BLACK_OOO,
    WHITE_CASTLE = WHITE_OO | WHITE_OOO,
    BLACK_CASTLE = BLACK_OO | BLACK_OOO,
    ANY_CASTLE = WHITE_CASTLE | BLACK_CASTLE
};

enum MoveFlags : uint16_t{
    NORMAL,
    PROMOTION = 1 << 14, // 0100 = KNIGHT, 0101 = BISHOP, 0110 = ROOK, 0111 = QUEEN;
    EN_PASSANT = 2 << 14,
    CASTLE = 3 << 14
};