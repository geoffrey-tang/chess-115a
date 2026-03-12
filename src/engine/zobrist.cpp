#include <cstdint>
#include <array>
#include "zobrist.h"
#include "constants.h"
#include "move_gen.h"

// Computes and returns a new Zobrist hash on the supplied Board
// Requires that Zobrist keys have been iniialized
uint64_t compute_zobrist(const Board& b){
    uint64_t hash = 0;

    for (int color = WHITE; color <= BLACK; color++) {
        for (int piece = PAWN; piece <= KING; piece++) {
            Bitboard bb = b.bb_pieces[color][piece];
            while (bb) {
                int sq = pop_lsb(bb);
                hash ^= Zobrist::piece_sq[color][piece][sq];
            }
        }
    }

    if(b.to_move == BLACK) hash ^= Zobrist::side_to_move;
    hash ^= Zobrist::castle[b.st->castle & 0xF];
    if(b.st->en_passant != 64) hash ^= Zobrist::ep_file[get_file(b.st->en_passant)];

    return hash;
}