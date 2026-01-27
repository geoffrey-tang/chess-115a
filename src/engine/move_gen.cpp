#include <cmath>
#include "move_gen.h"
#include "board.h"

Bitboard king_move(uint8_t square, Board& board, uint8_t color){
    Bitboard b = 0;
    for(int i : {-9, -8, -7, -1, 1, 7, 8, 9}){
        b |= check_dst(square, i);
    }
    return b & ~board.bb_colors[color];
}

Bitboard knight_move(uint8_t square, Board& board, uint8_t color){
    Bitboard b = 0;
    for(int i : {-17, -15, -10, -6, 6, 10, 15, 17}){
        b |= check_dst(square, i);
    }
    return b & ~board.bb_colors[color];
}

Bitboard bishop_move(uint8_t square, Board& board, uint8_t color){
    Bitboard b = 0;
    for(int i : {-9, -7, 7, 9}){
        uint8_t s = square;
        while(check_dst(s, i)){
            b |= (1ULL << (s += i));
            if((board.bb_colors[0] | board.bb_colors[1]) & (1ULL << s)){
                break;
            }
        }
    }
    return b & ~board.bb_colors[color];
}

Bitboard rook_move(uint8_t square, Board& board, uint8_t color){
    Bitboard b = 0;
    for(int i : {-8, -1, 1, 8}){
        uint8_t s = square;
        while(check_dst(s, i)){
            b |= (1ULL << (s += i));
            if((board.bb_colors[0] | board.bb_colors[1]) & (1ULL << s)){
                break;
            }
        }
    }
    return b & ~board.bb_colors[color];
}

Bitboard queen_move(uint8_t square, Board& board, uint8_t color){
    return bishop_move(square, board, color) | rook_move(square, board, color);
}

Bitboard pawn_move(uint8_t square, Board& board, uint8_t color){
    Bitboard empty = ~(board.bb_colors[0] | board.bb_colors[1]);
    Bitboard pawn_attacks = color == WHITE ? 
        (((1ULL << (square + 9)) & ~file_a_bb) | ((1ULL << (square + 7)) & ~file_h_bb)) & (board.bb_colors[BLACK] | (1ULL << board.en_passant)) :
        (((1ULL << (square - 9)) & ~file_h_bb) | ((1ULL << (square - 7)) & ~file_a_bb)) & (board.bb_colors[WHITE] | (1ULL << board.en_passant));
    Bitboard single_push = color == WHITE ? 
        ((1ULL << (square + 8)) & empty) :
        ((1ULL << (square - 8)) & empty);
    Bitboard double_push = color == WHITE ? 
        (single_push << 8) & empty & rank_4_bb :
        (single_push >> 8) & empty & rank_5_bb;
    return pawn_attacks | single_push | double_push;
}

std::vector<Move> generate_moves(Board& board, uint8_t color){
    std::vector<Move> movelist;
    uint8_t from, to;
    std::array<Bitboard, 6> pieces = board.bb_pieces[color];
    while(pieces[0]){
        from = pop_lsb(pieces[0]);
        Bitboard pawn = pawn_move(from, board, color);
        while(pawn){
            to = pop_lsb(pawn);
            movelist.push_back(set_move(from, to));
        }
    }
    while(pieces[1]){
        from = pop_lsb(pieces[1]);
        Bitboard knight = knight_move(from, board, color);
        while(knight){
            to = pop_lsb(knight);
            movelist.push_back(set_move(from, to));
        }
    }
    while(pieces[2]){
        from = pop_lsb(pieces[2]);
        Bitboard bishop = bishop_move(from, board, color);
        while(bishop){
            to = pop_lsb(bishop);
            movelist.push_back(set_move(from, to));
        }
    }
    while(pieces[3]){
        from = pop_lsb(pieces[3]);
        Bitboard rook = rook_move(from, board, color);
        while(rook){
            to = pop_lsb(rook);
            movelist.push_back(set_move(from, to));
        }
    }
    while(pieces[4]){
        from = pop_lsb(pieces[4]);
        Bitboard queen = queen_move(from, board, color);
        while(queen){
            to = pop_lsb(queen);
            movelist.push_back(set_move(from, to));
        }
    }
    while(pieces[5]){
        from = pop_lsb(pieces[5]);
        Bitboard king = king_move(from, board, color);
        while(king){
            to = pop_lsb(king);
            movelist.push_back(set_move(from, to));
        }
    }
    return movelist;
}

Bitboard check_dst(uint8_t square, int offset){
    uint8_t dst = square + offset;
    if(A1 <= dst && dst <= H8){
        return abs(int(get_file(square)) - int(get_file(dst))) <= 2 ? (1ULL << dst) : 0ULL;
    }
    else{
        return 0ULL;
    }
}

int lsb(Bitboard b){
    return __builtin_ctzll(b);
}

uint8_t pop_lsb(Bitboard& b){
    uint8_t sq = lsb(b);
    b &= b - 1;
    return sq;
}

/* might use this for magic bitboards later;
Bitboard rook_mask(uint8_t square){
    return (((file_a_bb << get_file(square)) | (rank_1_bb << (8 * get_rank(square)))) ^ (1ULL << square)) & ~rook_mask_file & ~rook_mask_rank;
}
*/