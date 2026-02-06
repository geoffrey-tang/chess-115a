#include <cmath>
#include "move_gen.h"
#include "board.h"
#include "constants.h"

Bitboard king_move(uint8_t square){ // refactor for params to accept a bitboard & color occupancy instead of Board and Color
    Bitboard b = 0;
    for(int i : {-9, -8, -7, -1, 1, 7, 8, 9}){
        b |= check_dst(square, i);
    }
    return b;
}

Bitboard knight_move(uint8_t square){
    Bitboard b = 0;
    for(int i : {-17, -15, -10, -6, 6, 10, 15, 17}){
        b |= check_dst(square, i);
    }
    return b;
}

Bitboard bishop_move(uint8_t square, Bitboard occupancy){
    Bitboard b = 0;
    for(int i : {-9, -7, 7, 9}){
        uint8_t s = square;
        while(check_dst(s, i)){
            b |= (1ULL << (s += i));
            if(occupancy & (1ULL << s)){
                break;
            }
        }
    }
    return b;
}


Bitboard rook_move(uint8_t square, Bitboard occupancy){
    Bitboard b = 0;
    for(int i : {-8, -1, 1, 8}){
        uint8_t s = square;
        while(check_dst(s, i)){
            b |= (1ULL << (s += i));
            if(occupancy & (1ULL << s)){
                break;
            }
        }
    }
    return b;
}

Bitboard queen_move(uint8_t square, Bitboard occupancy){
    return bishop_move(square, occupancy) | rook_move(square, occupancy);
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

bool square_attacked(Board& board, int sq, uint8_t by_color) {
    Bitboard occ = board.bb_colors[WHITE] | board.bb_colors[BLACK];
    Bitboard target = 1ULL << sq;

    Bitboard pawns = board.bb_pieces[by_color][PAWN];
    Bitboard pawnAtt = 0ULL;

    if (by_color == WHITE) {
        pawnAtt |= (pawns << 7) & ~file_h_bb;
        pawnAtt |= (pawns << 9) & ~file_a_bb;
    } else {
        pawnAtt |= (pawns >> 7) & ~file_a_bb;
        pawnAtt |= (pawns >> 9) & ~file_h_bb;
    }
    if (pawnAtt & target) return true;

    Bitboard knights = board.bb_pieces[by_color][KNIGHT];
    while (knights) {
        int from = pop_lsb(knights);
        if (knight_move(from) & target) return true;
    }

    Bitboard bishops = board.bb_pieces[by_color][BISHOP] | board.bb_pieces[by_color][QUEEN];
    while (bishops) {
        int from = pop_lsb(bishops);
        if (bishop_move(from, occ) & target) return true;
    }

    Bitboard rooks = board.bb_pieces[by_color][ROOK] | board.bb_pieces[by_color][QUEEN];
    while (rooks) {
        int from = pop_lsb(rooks);
        if (rook_move(from, occ) & target) return true;
    }

    Bitboard king = board.bb_pieces[by_color][KING];
    if (king) {
        int from = lsb(king);
        if (king_move(from) & target) return true;
    }

    return false;
}

std::vector<Move> generate_moves(Board& board, uint8_t color){ // this solution feels awful; find a more elegant way in fewer lines if time permits
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
        Bitboard knight = knight_move(from) & ~board.bb_colors[color];
        while(knight){
            to = pop_lsb(knight);
            movelist.push_back(set_move(from, to));
        }
    }
    while(pieces[2]){
        from = pop_lsb(pieces[2]);
        Bitboard bishop = bishop_move(from, board.bb_colors[0] | board.bb_colors[1]) & ~board.bb_colors[color];
        while(bishop){
            to = pop_lsb(bishop);
            movelist.push_back(set_move(from, to));
        }
    }
    while(pieces[3]){
        from = pop_lsb(pieces[3]);
        Bitboard rook = rook_move(from, board.bb_colors[0] | board.bb_colors[1]) & ~board.bb_colors[color];
        while(rook){
            to = pop_lsb(rook);
            movelist.push_back(set_move(from, to));
        }
    }
    while(pieces[4]){
        from = pop_lsb(pieces[4]);
        Bitboard queen = queen_move(from, board.bb_colors[0] | board.bb_colors[1]) & ~board.bb_colors[color];
        while(queen){
            to = pop_lsb(queen);
            movelist.push_back(set_move(from, to));
        }
    }
    while(pieces[5]){
        from = pop_lsb(pieces[5]);
        Bitboard king = king_move(from) & ~board.bb_colors[color];
        while(king){
            to = pop_lsb(king);
            movelist.push_back(set_move(from, to));
        }
    }
    if(board.castle){ // yanderedev tier code; update to a more elegant solution
        if(color == WHITE){
            if(board.castle & WHITE_CASTLE || board.castle & WHITE_OO){
                if(!square_attacked(board, E1, BLACK) && !square_attacked(board, F1, BLACK) && !square_attacked(board, G1, BLACK) && !(castle_path[0] & (board.bb_colors[WHITE] | board.bb_colors[BLACK]))){
                    movelist.push_back(set_move(E1, G1)); // set flags later
                }
            }
            if(board.castle & WHITE_CASTLE || board.castle & WHITE_OOO){
                if(!square_attacked(board, E1, BLACK) && !square_attacked(board, D1, BLACK) && !square_attacked(board, C1, BLACK) && !(castle_path[1] & (board.bb_colors[WHITE] | board.bb_colors[BLACK]))){
                    movelist.push_back(set_move(E1, C1));
                }
            }
        }
        else{
            if(board.castle & BLACK_CASTLE || board.castle & BLACK_OO){
                if(!square_attacked(board, E8, WHITE) && !square_attacked(board, F8, WHITE) && !square_attacked(board, G8, WHITE) && !(castle_path[2] & (board.bb_colors[WHITE] | board.bb_colors[BLACK]))){
                    movelist.push_back(set_move(E8, G8));
                }
            }
            if(board.castle & BLACK_CASTLE || board.castle & BLACK_OOO){
                if(!square_attacked(board, E8, WHITE) && !square_attacked(board, D8, WHITE) && !square_attacked(board, C8, WHITE) && !(castle_path[3] & (board.bb_colors[WHITE] | board.bb_colors[BLACK]))){
                    movelist.push_back(set_move(E8, C8));
                }
            }
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

/* might use this for magic bitboards later
Bitboard rook_mask(uint8_t square){
    return (((file_a_bb << get_file(square)) | (rank_1_bb << (8 * get_rank(square)))) ^ (1ULL << square)) & ~rook_mask_file & ~rook_mask_rank;
}
*/