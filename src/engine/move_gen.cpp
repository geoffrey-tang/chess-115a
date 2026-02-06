#include <cmath>
#include <cassert>
#include "move_gen.h"
#include "board.h"
#include "constants.h"
#include "search.h"

// Generates king attack bitboard, assuming no friendlies
Bitboard king_move(uint8_t square){ 
    Bitboard b = 0;
    for(int i : {-9, -8, -7, -1, 1, 7, 8, 9}){
        b |= check_dst(square, i);
    }
    return b;
}

// Generates knight attack bitboard, assuming no friendlies
Bitboard knight_move(uint8_t square){
    Bitboard b = 0;
    for(int i : {-17, -15, -10, -6, 6, 10, 15, 17}){
        b |= check_dst(square, i);
    }
    return b;
}

// Generates bishop attack bitboard, assuming no friendlies
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

// Generates rook attack bitboard, assuming no friendlies
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

// Generates queen attack bitboard, assuming no friendlies
Bitboard queen_move(uint8_t square, Bitboard occupancy){
    return bishop_move(square, occupancy) | rook_move(square, occupancy);
}

// Generates pawn attack bitboard
Bitboard pawn_move(uint8_t square, Board& board, uint8_t color){
    Bitboard empty = ~(board.bb_colors[0] | board.bb_colors[1]);
    Bitboard moves = 0ULL;
    if(color == WHITE){
        // capture
        moves |= check_dst(square, 7) & (board.bb_colors[BLACK]);
        moves |= check_dst(square, 9) & (board.bb_colors[BLACK]);
        if (board.st->en_passant < 64) {
            Bitboard ep_bb = 1ULL << board.st->en_passant;
            moves |= (check_dst(square, 7) | check_dst(square, 9)) & ep_bb;
        }

        // single push
        Bitboard single_push = check_dst(square, 8) & empty;
        moves |= single_push;

        // double push
        if (single_push) {
            Bitboard double_push = check_dst(square, 16) & empty & rank_4_bb;
            moves |= double_push;
        }
    }
    else{
        // capture
        moves |= check_dst(square, -7) & (board.bb_colors[WHITE]);
        moves |= check_dst(square, -9) & (board.bb_colors[WHITE]);
        if (board.st->en_passant < 64) {
            Bitboard ep_bb = 1ULL << board.st->en_passant;
            moves |= (check_dst(square, -7) | check_dst(square, -9)) & ep_bb;
        }

        // single push
        Bitboard single_push = check_dst(square, -8) & empty;
        moves |= single_push;

        // double push
        if (single_push) {
            Bitboard double_push = check_dst(square, -16) & empty & rank_5_bb;
            moves |= double_push;
        }
    }
    return moves;
}

// Generates a vector of pseudo-legal moves (basic movement, but not necessarily legal)
std::vector<Move> generate_pseudo(Board& board, uint8_t color){ // this solution feels awful; find a more elegant way in fewer lines if time permits
    std::vector<Move> movelist;
    uint8_t from, to;
    std::array<Bitboard, 6> pieces = board.bb_pieces[color];
    while(pieces[0]){
        from = pop_lsb(pieces[0]);
        Bitboard pawn = pawn_move(from, board, color);
        while(pawn){
            to = pop_lsb(pawn);
            if(to == board.st->en_passant) movelist.push_back(set_move(from, to, EN_PASSANT));
            else if(to >= 56 && to <= 63 && color == WHITE){
                movelist.push_back(set_move(from, to, PROMOTION | ((KNIGHT - 1) << 12)));
                movelist.push_back(set_move(from, to, PROMOTION | ((BISHOP - 1) << 12)));
                movelist.push_back(set_move(from, to, PROMOTION | ((ROOK - 1) << 12)));
                movelist.push_back(set_move(from, to, PROMOTION | ((QUEEN - 1) << 12)));
            }
            else if(to <= 7 && color == BLACK){
                movelist.push_back(set_move(from, to, PROMOTION | ((KNIGHT - 1) << 12)));
                movelist.push_back(set_move(from, to, PROMOTION | ((BISHOP - 1) << 12)));
                movelist.push_back(set_move(from, to, PROMOTION | ((ROOK - 1) << 12)));
                movelist.push_back(set_move(from, to, PROMOTION | ((QUEEN - 1) << 12)));
            }
            else movelist.push_back(set_move(from, to, NORMAL));
        }
    }
    while(pieces[1]){
        from = pop_lsb(pieces[1]);
        Bitboard knight = knight_move(from) & ~board.bb_colors[color];
        while(knight){
            to = pop_lsb(knight);
            movelist.push_back(set_move(from, to, NORMAL));
        }
    }
    while(pieces[2]){
        from = pop_lsb(pieces[2]);
        Bitboard bishop = bishop_move(from, board.bb_colors[0] | board.bb_colors[1]) & ~board.bb_colors[color];
        while(bishop){
            to = pop_lsb(bishop);
            movelist.push_back(set_move(from, to, NORMAL));
        }
    }
    while(pieces[3]){
        from = pop_lsb(pieces[3]);
        Bitboard rook = rook_move(from, board.bb_colors[0] | board.bb_colors[1]) & ~board.bb_colors[color];
        while(rook){
            to = pop_lsb(rook);
            movelist.push_back(set_move(from, to, NORMAL));
        }
    }
    while(pieces[4]){
        from = pop_lsb(pieces[4]);
        Bitboard queen = queen_move(from, board.bb_colors[0] | board.bb_colors[1]) & ~board.bb_colors[color];
        while(queen){
            to = pop_lsb(queen);
            movelist.push_back(set_move(from, to, NORMAL));
        }
    }
    while(pieces[5]){
        from = pop_lsb(pieces[5]);
        Bitboard king = king_move(from) & ~board.bb_colors[color];
        while(king){
            to = pop_lsb(king);
            movelist.push_back(set_move(from, to, NORMAL));
        }
    }
    if(board.st->castle){ // yanderedev tier code; update to a more elegant solution
        if((color == WHITE) && (board.bb_pieces[WHITE][KING] & (1ULL << E1))){
            if( (board.st->castle & WHITE_OO) && (board.bb_pieces[WHITE][ROOK] & (1ULL << H1))){
                if(!square_attacked(board, E1, BLACK) && !square_attacked(board, F1, BLACK) && !square_attacked(board, G1, BLACK) && !(castle_path[0] & (board.bb_colors[WHITE] | board.bb_colors[BLACK]))){
                    movelist.push_back(set_move(E1, G1, CASTLE)); // set flags later
                }
            }
            if( (board.st->castle & WHITE_OOO) && (board.bb_pieces[WHITE][ROOK] & (1ULL << A1))){
                if(!square_attacked(board, E1, BLACK) && !square_attacked(board, D1, BLACK) && !square_attacked(board, C1, BLACK) && !(castle_path[1] & (board.bb_colors[WHITE] | board.bb_colors[BLACK]))){
                    movelist.push_back(set_move(E1, C1, CASTLE));
                }
            }
        }
        else if((color == BLACK) && (board.bb_pieces[BLACK][KING] & (1ULL << E8))){
            if( (board.st->castle & BLACK_OO) && (board.bb_pieces[BLACK][ROOK] & (1ULL << H8)) ){
                if(!square_attacked(board, E8, WHITE) && !square_attacked(board, F8, WHITE) && !square_attacked(board, G8, WHITE) && !(castle_path[2] & (board.bb_colors[WHITE] | board.bb_colors[BLACK]))){
                    movelist.push_back(set_move(E8, G8, CASTLE));
                }
            }
            if( (board.st->castle & BLACK_OOO) && (board.bb_pieces[BLACK][ROOK] & (1ULL << A8))){
                if(!square_attacked(board, E8, WHITE) && !square_attacked(board, D8, WHITE) && !square_attacked(board, C8, WHITE) && !(castle_path[3] & (board.bb_colors[WHITE] | board.bb_colors[BLACK]))){
                    movelist.push_back(set_move(E8, C8, CASTLE));
                }
            }
        }
    }
    return movelist;
}

// Generate the list of legal moves in a position
std::vector<Move> generate_moves(Board& board, StateStack& ss){
    std::vector<Move> pseudo = generate_pseudo(board, board.to_move);
    std::vector<Move> legal_moves;
    legal_moves.reserve(pseudo.size());
    for(Move m : pseudo){
        if(legal(board, ss, m)){
            legal_moves.push_back(m);
        }
    }
    return legal_moves;
}

// Plays a move, and pushes it onto the search stack
void do_move(Board& board, StateStack& ss, Move move){
    uint8_t color = board.to_move;
    uint8_t from = get_from_sq(move);
    uint8_t to = get_to_sq(move);
    uint8_t moved_piece = piece_on_square(board, color, from);
    assert(moved_piece != NONE);

    // define a new board state & push onto stack
    BoardState* new_st = &ss.states[++ss.ply];
    new_st->previous   = board.st;
    new_st->castle     = board.st->castle;
    new_st->en_passant = 64; //clear en passant by default
    new_st->halfmove   = board.st->halfmove;
    new_st->fullmove   = board.st->fullmove;
    new_st->captured_piece  = NONE;
    new_st->captured_square = to;

    board.st = new_st;

    Bitboard from_bb = 1ULL << from;
    Bitboard to_bb = 1ULL << to;
    bool capture = (board.bb_colors[!color] & to_bb) != 0;

    board.st->halfmove = (moved_piece == PAWN || capture) ? 0 : (board.st->halfmove + 1);

    // handle en passant captures, normal captures, and non-captures
    if(get_move_flags(move) == (EN_PASSANT >> 14)){ // ok flags might need to be changed bc right now its X << 14 but get_move_flags returns a 4 bit thingy which won't evaluate to be the same
        uint8_t cap_sq = (color == WHITE) ? uint8_t(to - 8) : uint8_t(to + 8);
        board.st->captured_square = cap_sq;
        board.st->captured_piece = PAWN;
        Bitboard cap_bb = 1ULL << cap_sq;
        board.bb_pieces[!color][PAWN] ^= cap_bb;
        board.bb_colors[!color] ^= cap_bb;
    }
    else if(capture){
        uint8_t cap_piece = piece_on_square(board, !color, to);
        board.st->captured_piece = cap_piece;
        board.bb_pieces[!color][cap_piece] ^= to_bb;
        board.bb_colors[!color] ^= to_bb;
    }
    board.bb_pieces[color][moved_piece] ^= (from_bb | to_bb);
    board.bb_colors[color] ^= (from_bb | to_bb);

    // handle promotions
    if(parse_promotion_flag(move) != NONE){
        uint8_t promo_piece = parse_promotion_flag(move);
        board.bb_pieces[color][PAWN] ^= to_bb;
        board.bb_pieces[color][promo_piece] ^= to_bb;
    }

    // move rooks during castling
    if(get_move_flags(move) == CASTLE >> 14){
        if(color == WHITE){
            if(to == G1){
                Bitboard rook_from = 1ULL << H1;
                Bitboard rook_to = 1ULL << F1;
                board.bb_pieces[WHITE][ROOK] ^= (rook_from | rook_to);
                board.bb_colors[WHITE] ^= (rook_from | rook_to);
            }
            else if (to == C1){
                Bitboard rook_from = 1ULL << A1;
                Bitboard rook_to = 1ULL << D1;
                board.bb_pieces[WHITE][ROOK] ^= (rook_from | rook_to);
                board.bb_colors[WHITE] ^= (rook_from | rook_to);
            }
        }
        else{
            if(to == G8){
                Bitboard rook_from = 1ULL << H8;
                Bitboard rook_to = 1ULL << F8;
                board.bb_pieces[BLACK][ROOK] ^= (rook_from | rook_to);
                board.bb_colors[BLACK] ^= (rook_from | rook_to);
            }
            else if (to == C8){
                Bitboard rook_from = 1ULL << A8;
                Bitboard rook_to = 1ULL << D8;
                board.bb_pieces[BLACK][ROOK] ^= (rook_from | rook_to);
                board.bb_colors[BLACK] ^= (rook_from | rook_to);
            }
        }
    }

    // set en passant if double push pawn
    if(moved_piece == PAWN){
        if(color == WHITE && to == uint8_t(from + 16)){
            board.st->en_passant = uint8_t(from + 8);
        }
        else if(color == BLACK && from == uint8_t(to + 16)){
            board.st->en_passant = uint8_t(from - 8);
        }
    }

    update_castling(board, color, moved_piece, move, *board.st);
    if(color == BLACK) board.st->fullmove++;

    board.to_move = !color;
}

// Reverts a move to the previous position on the stack. 
// Note that the move parameter assumes that the exact correct move is put in, but this should be fine as we only really want to do this during searching so we'll know the exact move
void undo_move(Board& board, StateStack& ss, Move move){
    // reset side
    board.to_move ^= 1;
    uint8_t color = board.to_move;
    uint8_t from = get_from_sq(move);
    uint8_t to = get_to_sq(move);
    Bitboard from_bb = 1ULL << from;
    Bitboard to_bb = 1ULL << to;

    // undo castling
    if(get_move_flags(move) == CASTLE >> 14){
        if(color == WHITE){
            if(to == G1){
                Bitboard rook_from = 1ULL << H1;
                Bitboard rook_to = 1ULL << F1;
                board.bb_pieces[WHITE][ROOK] ^= (rook_from | rook_to);
                board.bb_colors[WHITE] ^= (rook_from | rook_to);
            }
            else if (to == C1){
                Bitboard rook_from = 1ULL << A1;
                Bitboard rook_to = 1ULL << D1;
                board.bb_pieces[WHITE][ROOK] ^= (rook_from | rook_to);
                board.bb_colors[WHITE] ^= (rook_from | rook_to);
            }
        }
        else{
            if(to == G8){
                Bitboard rook_from = 1ULL << H8;
                Bitboard rook_to = 1ULL << F8;
                board.bb_pieces[BLACK][ROOK] ^= (rook_from | rook_to);
                board.bb_colors[BLACK] ^= (rook_from | rook_to);
            }
            else if (to == C8){
                Bitboard rook_from = 1ULL << A8;
                Bitboard rook_to = 1ULL << D8;
                board.bb_pieces[BLACK][ROOK] ^= (rook_from | rook_to);
                board.bb_colors[BLACK] ^= (rook_from | rook_to);
            }
        }
    }

    // undo promotion (swap back to pawn)
    if(parse_promotion_flag(move) != NONE){
        uint8_t promo_piece = parse_promotion_flag(move);
        board.bb_pieces[color][PAWN] ^= to_bb;
        board.bb_pieces[color][promo_piece] ^= to_bb;
    }

    // undo move
    uint8_t moved_piece = piece_on_square(board, color, to);
    board.bb_pieces[color][moved_piece] ^= (from_bb | to_bb);
    board.bb_colors[color] ^= (from_bb | to_bb);
    
    // restore captured piece
    if (board.st->captured_piece != NONE) {
        uint64_t cap_bb = 1ULL << board.st->captured_square;
        board.bb_pieces[!color][board.st->captured_piece] ^= cap_bb;
        board.bb_colors[!color] ^= cap_bb;
    }

    // pop BoardState
    board.st = board.st->previous;
    ss.ply--;
}

// Get the square that a certain color's king is on, assuming only 1 king
uint8_t king_square(Board& board, uint8_t color) {
    Bitboard kbb = board.bb_pieces[color][KING];
    return (uint8_t)__builtin_ctzll(kbb);
}

// Check if a square is attacked by a certain color
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

// Update castling rights after a move. st assumes that the Board's current BoardState has already been updated, so only use after a move is done
void update_castling(Board& board, uint8_t color, uint8_t moved_piece, Move move, BoardState& st){
    if(moved_piece == KING){
        if (color == WHITE) board.st->castle &= ~(WHITE_CASTLE);
        else board.st->castle &= ~(BLACK_CASTLE);
    }
    else if(moved_piece == ROOK){
        if (color == WHITE) {
            if (get_from_sq(move) == A1) board.st->castle &= ~WHITE_OOO;
            if (get_from_sq(move) == H1) board.st->castle &= ~WHITE_OO; 
        } 
        else {
            if (get_from_sq(move) == A8) board.st->castle &= ~BLACK_OOO;
            if (get_from_sq(move) == H8) board.st->castle &= ~BLACK_OO; 
        }
    }
    else if(st.captured_piece == ROOK){
        uint8_t cap_sq = st.captured_square;
        if (color == BLACK) {
            if (cap_sq == A1) board.st->castle &= ~WHITE_OOO;
            if (cap_sq == H1) board.st->castle &= ~WHITE_OO;
        } else {
            if (cap_sq == A8) board.st->castle &= ~BLACK_OOO;
            if (cap_sq == H8) board.st->castle &= ~BLACK_OO;
        }
    }
}

// Checks a move for legality
bool legal(Board& board, StateStack& ss, Move move){
    // this solution is definitely really slow but we just want correctness for now; optimize later
    uint8_t color = board.to_move;
    do_move(board, ss, move);
    bool in_check = square_attacked(board, king_square(board, color), !color);
    undo_move(board, ss, move);
    return !in_check;
}

// Check if the destination square is a valid destination
Bitboard check_dst(int square, int offset){
    int dst = square + offset;
    if(A1 <= dst && dst <= H8){
        int file_sq = int(get_file((uint8_t)square));
        int file_dst = int(get_file((uint8_t)dst));
        return abs(file_sq - file_dst) <= 2 ? (1ULL << dst) : 0ULL;
    }
    else{
        return 0ULL;
    }
}

// Gets the index of the first non-zero bit
int lsb(Bitboard b){
    return __builtin_ctzll(b);
}

// Gets the first non-zero square on a bitboard, then pops the bit from the bitboard
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

/*
OLD (broken) legal() code
    uint64_t from = 1ULL << get_from_sq(move);
    uint64_t to = 1ULL << get_to_sq(move);
    uint8_t flags = get_move_flags(move);
    uint8_t king = lsb(board.bb_pieces[board.to_move][king]);

    // special en passant check; check for any discovered checks
    if(flags == EN_PASSANT){
        uint8_t capture_dir = board.to_move == WHITE ? board.st->en_passant >> 8 : board.st->en_passant << 8;
        uint64_t capture_sq = 1ULL << capture_dir;
        Bitboard occupy = ((board.bb_colors[WHITE] | board.bb_colors[BLACK]) ^ from ^ capture_sq) | to;

        // return ortho + diagonal bitboards' overlap with rooks + bishops + queens
        return !(rook_move(king, occupy) & (board.bb_pieces[!board.to_move][ROOK] | board.bb_pieces[!board.to_move][QUEEN])) 
            && !(bishop_move(king, occupy) & (board.bb_pieces[!board.to_move][BISHOP] | board.bb_pieces[!board.to_move][QUEEN]));
    }
    
    // castling has been pre-checked in generate_move; if castling check is refactored change this

    // check other moves if they result in self-check
    if(from == king){
        Bitboard occupy = ((board.bb_colors[WHITE] | board.bb_colors[BLACK]) ^ from) | to;
        return !square_attacked(board, to, !board.to_move);
    }
    else{
        Bitboard occupy = ((board.bb_colors[WHITE] | board.bb_colors[BLACK]) ^ from) | to;
        return !square_attacked(board, king, !board.to_move);
    }
*/