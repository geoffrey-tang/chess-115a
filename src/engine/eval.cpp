#include "eval.h"
#include "constants.h"

static inline int popcount(Bitboard bb) {
    return __builtin_popcountll(bb);
}

// pop least significant 1-bit and return its index [0..63]
static inline int pop_lsb(Bitboard& bb) {
    int sq = __builtin_ctzll(bb);
    bb &= (bb - 1);
    return sq;
}

// mirror square vertically for black PST (A1<->A8 etc.)
static inline int mirror_sq(int sq) {
    return sq ^ 56;
}

// TEMP PSTs (all zeros for now) replace later with real tables.
static const int PST_PAWN[64] = { 0 };
static const int PST_KNIGHT[64] = { 0 };
static const int PST_BISHOP[64] = { 0 };
static const int PST_ROOK[64] = { 0 };
static const int PST_QUEEN[64] = { 0 };
static const int PST_KING[64] = { 0 };

static int piece_square_score(const Board& b) {
    int score = 0;

    for (int p = PAWN; p <= KING; p++) {
        const int* pst = nullptr;

        if (p == PAWN) {
            pst = PST_PAWN;
        } else if (p == KNIGHT) {
            pst = PST_KNIGHT;
        } else if (p == BISHOP) {
            pst = PST_BISHOP;
        } else if (p == ROOK) {
            pst = PST_ROOK;
        } else if (p == QUEEN) {
            pst = PST_QUEEN;
        } else if (p == KING) {
            pst = PST_KING;
        }

        // white pieces add PST directly
        {
            Bitboard bb = b.bb_pieces[WHITE][p];
            while (bb) {
                int sq = pop_lsb(bb);
                score += pst[sq];
            }
                }

        // black pieces subtract PST using mirrored square index
        {
            Bitboard bb = b.bb_pieces[BLACK][p];
            while (bb) {
                int sq = pop_lsb(bb);
                int msq = mirror_sq(sq);
                score -= pst[msq];
            }
        }
    }

    return score;
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

int evaluate(const Board& b) {
    int score = 0;

    score += material_score(b);
    score += piece_square_score(b);

    return score;
}