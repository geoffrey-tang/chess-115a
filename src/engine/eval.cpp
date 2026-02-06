#include "eval.h"
#include "constants.h"

static inline int popcount(Bitboard bb) {
    return __builtin_popcountll(bb);
}

int material_score(const Board& b) {
    // Centipawn values (common defaults)
    static constexpr int V[6] = {
        100, // PAWN
        320, // KNIGHT
        330, // BISHOP
        500, // ROOK
        900, // QUEEN
        0    // KING
    };

    int score = 0;
    for (int p = PAWN; p <= KING; p++) {
        int w = popcount(b.bb_pieces[WHITE][p]);
        int bl = popcount(b.bb_pieces[BLACK][p]);
        score += V[p] * (w - bl);
    }
    return score; // + => white ahead, - => black ahead
}
