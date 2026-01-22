#pragma once

#include <cstdint>

#define LAST_BIT 63

using Bitboard = uint64_t;

constexpr Bitboard file_a_bb = 0x8080808080808080ULL;
constexpr Bitboard file_b_bb = file_a_bb >> 1;
constexpr Bitboard file_c_bb = file_a_bb >> 2;
constexpr Bitboard file_d_bb = file_a_bb >> 3;
constexpr Bitboard file_e_bb = file_a_bb >> 4;
constexpr Bitboard file_f_bb = file_a_bb >> 5;
constexpr Bitboard file_g_bb = file_a_bb >> 6;
constexpr Bitboard file_h_bb = file_a_bb >> 7;

constexpr Bitboard rank_1_bb = 0xFF;
constexpr Bitboard rank_2_bb = rank_1_bb << (8 * 1);
constexpr Bitboard rank_3_bb = rank_1_bb << (8 * 2);
constexpr Bitboard rank_4_bb = rank_1_bb << (8 * 3);
constexpr Bitboard rank_5_bb = rank_1_bb << (8 * 4);
constexpr Bitboard rank_6_bb = rank_1_bb << (8 * 5);
constexpr Bitboard rank_7_bb = rank_1_bb << (8 * 6);
constexpr Bitboard rank_8_bb = rank_1_bb << (8 * 7);

enum Squares : uint8_t { // from LSB to MSB
    H1, G1, F1, E1, D1, C1, B1, A1,
    H2, G2, F2, E2, D2, C2, B2, A2,
    H3, G3, F3, E3, D3, C3, B3, A3,
    H4, G4, F4, E4, D4, C4, B4, A4,
    H5, G5, F5, E5, D5, C5, B5, A5,
    H6, G6, F6, E6, D6, C6, B6, A6,
    H7, G7, F7, E7, D7, C7, B7, A7,
    H8, G8, F8, E8, D8, C8, B8, A8
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