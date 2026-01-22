#pragma once

#include <cstdint>

#define LAST_BIT 63

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