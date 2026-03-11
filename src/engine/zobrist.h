# pragma once

#include "board.h"

// https://rosettacode.org/wiki/Pseudo-random_numbers/Splitmix64
// 64-bit PRNG
struct SplitMix64 {
    uint64_t x; // current state

    explicit SplitMix64(uint64_t seed)  // constructor
        : x(seed) {}

    uint64_t next() { // get next pseudorandom number
        uint64_t z = (x += 0x9E3779B97F4A7C15ULL);
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
        z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
        return z ^ (z >> 31);
    }
};

namespace Zobrist{
    inline std::array<std::array<std::array<uint64_t, 64>, 6>, 2> piece_sq{};
    inline uint64_t side_to_move = 0;          
    inline std::array<uint64_t, 16> castle{};  // 0..15 rights mask
    inline std::array<uint64_t, 8> ep_file{};  // file a..h (0..7)

    inline void init(uint64_t seed = 0xC0FFEE123456789ULL) {
        SplitMix64 rng(seed);

        for (int color = WHITE; color <= BLACK; color++)
            for (int piece = PAWN; piece <= KING; piece++)
                for (int sq = A1; sq <= H8; sq++)
                    piece_sq[color][piece][sq] = rng.next();

        side_to_move = rng.next();

        for (int i = 0; i < 16; ++i) castle[i] = rng.next();
        for (int f = 0; f < 8; ++f)  ep_file[f] = rng.next();
    }
}

uint64_t compute_zobrist(const Board& b);