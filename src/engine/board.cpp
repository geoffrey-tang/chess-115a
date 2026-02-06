#include <iostream>
#include <cstdint>
#include <string>
#include <vector>
#include <bitset>
#include <iterator>
#include <algorithm>
#include "board.h"
#include "move_gen.h"
#include "constants.h"

Bitboard line_bb[64][64];
Bitboard between_bb[64][64]; 
Bitboard ray_bb[64][64];
Bitboard castle_path[4] = {3ULL << F1, 7ULL << B1, 3ULL << F8, 7ULL << B8};

// Initializing constants & lookup tables (not done)
void init(){
    for(int sq1 = A1; sq1 <= H8; sq1++){
        for(int sq2 = A1; sq2 <= H8; sq2++){
            if(rook_move(sq1, 0) & (1ULL << sq2)){
                line_bb[sq1][sq2] = (rook_move(sq1, 0) & rook_move(sq2, 0)) | (1ULL << sq1) | (1ULL << sq2);
                between_bb[sq1][sq2] = (rook_move(sq1, (1ULL << sq2)) & rook_move(sq2, (1ULL << sq1)));
                ray_bb[sq1][sq2] = (rook_move(sq1, 0) & rook_move(sq2, (1ULL << sq1))) | (1ULL << sq2);
            }
            if(bishop_move(sq1, 0) & (1ULL << sq2)){
                line_bb[sq1][sq2] = (bishop_move(sq1, 0) & bishop_move(sq2, 0)) | (1ULL << sq1) | (1ULL << sq2);
                between_bb[sq1][sq2] = (bishop_move(sq1, (1ULL << sq2)) & bishop_move(sq2, (1ULL << sq1)));
                ray_bb[sq1][sq2] = (bishop_move(sq1, 0) & bishop_move(sq2, (1ULL << sq1))) | (1ULL << sq2);
            }
        }
    }
}

// Print a single bitboard in an 8x8 grid
void print_bitboard(Bitboard bitboard){
    for(int rank = 7; rank >= 0; rank--){
        for(int file = 0; file < 8; file++){
            uint64_t mask = get_mask(rank, file);
            char c = (bitboard & mask) ? '1' : '0';
            std::cout << c << ' ';
        }
        std::cout << '\n';
    }
}

// Print a full Board position, along with state info
void print_board(Board board){
    char c;
    for(int rank = 7; rank >= 0; rank--){
        std::cout << rank + 1 << "|";
        for(int file = 0; file < 8; file++){
            uint64_t mask = get_mask(rank, file);
            c = '+';
            for(int color = 0; color < 2; color++){
                for(int piece = 0; piece < 6; piece++){
                    if (board.bb_pieces[color][piece] & mask){
                        if(color == 0){
                            switch(piece){
                                case PAWN:
                                    c = 'P';
                                    break;
                                case KNIGHT:
                                    c = 'N';
                                    break;
                                case BISHOP:
                                    c = 'B';
                                    break;
                                case ROOK:
                                    c = 'R';
                                    break;
                                case QUEEN:
                                    c = 'Q';
                                    break;
                                case KING:
                                    c = 'K';
                                    break;
                            }
                        }
                        else{
                            switch(piece){
                                case PAWN:
                                    c = 'p';
                                    break;
                                case KNIGHT:
                                    c = 'n';
                                    break;
                                case BISHOP:
                                    c = 'b';
                                    break;
                                case ROOK:
                                    c = 'r';
                                    break;
                                case QUEEN:
                                    c = 'q';
                                    break;
                                case KING:
                                    c = 'k';
                                    break;
                            }
                        }
                    }
                }
            }
            std::cout << c << ' ';
        }
        std::cout << '\n';
    }
    std::cout << "  ---------------\n  a b c d e f g h\n";
    std::cout << (board.to_move ? "Black" : "White") << " to move\n";
    std::cout << "Castling (B_OOO, B_OO, W_OOO, W_OO): " << std::bitset<4>(board.st->castle) << "\n";
    std::cout << "En passant: " << (board.st->en_passant != 64 ? int_to_algebraic(board.st->en_passant) : "-") << "\n";
    std::cout << "50-move halfmove counter: " << board.st->halfmove << "\n";
    std::cout << "Turn: " << board.st->fullmove << "\n";
}

// Generate and print the legal movelist for the given Board
void print_moves(Board& board, StateStack& ss){
    std::vector<Move> movelist = generate_moves(board, ss);
    std::cout << movelist.size() << " MOVES:\n";
    for(Move i : movelist){
        std::cout << int_to_algebraic(get_from_sq(i)) << int_to_algebraic(get_to_sq(i)) << " " << std::bitset<2>(get_move_flags(i));
        switch(parse_promotion_flag(i)){
            case KNIGHT: std::cout << " KNIGHT\n"; break;
            case BISHOP: std::cout << " BISHOP\n"; break;
            case ROOK: std::cout << " ROOK\n"; break;
            case QUEEN: std::cout << " QUEEN\n"; break;
            default: std::cout << "\n"; break;
        }
    }
}

// Parse a FEN string into its 6 constituent parts
std::vector<std::string> fen_parse(std::string fen){
    std::vector<std::string> fen_parts;
    std::string token;
    size_t pos = 0;
    while((pos = fen.find(" ")) != std::string::npos){
        token = fen.substr(0, pos);
        fen_parts.push_back(token);
        fen.erase(0, pos + 1);
    }
    fen_parts.push_back(fen);
    return fen_parts;
}

// Use previously parsed FEN string to generate bitboards
void get_bb_from_fen_pieces(std::string fen_pieces, Board& bitboards){
    uint64_t file = 0;
    uint64_t rank = 7;
    for(size_t i = 0; i < fen_pieces.length(); i++){
        uint64_t mask = get_mask(rank, file);
        switch(fen_pieces[i]){
            case 'P': 
                bitboards.bb_pieces[0][PAWN] |= mask;
                bitboards.bb_colors[0] |= mask;
                file++;
                break;
            case 'N': 
                bitboards.bb_pieces[0][KNIGHT] |= mask;
                bitboards.bb_colors[0] |= mask;
                file++;
                break;
            case 'B': 
                bitboards.bb_pieces[0][BISHOP] |= mask;
                bitboards.bb_colors[0] |= mask;
                file++;
                break;
            case 'R': 
                bitboards.bb_pieces[0][ROOK] |= mask;
                bitboards.bb_colors[0] |= mask;
                file++;
                break;
            case 'Q': 
                bitboards.bb_pieces[0][QUEEN] |= mask;
                bitboards.bb_colors[0] |= mask;
                file++;
                break;
            case 'K': 
                bitboards.bb_pieces[0][KING] |= mask;
                bitboards.bb_colors[0] |= mask;
                file++;
                break;

            case 'p': 
                bitboards.bb_pieces[1][PAWN] |= mask;
                bitboards.bb_colors[1] |= mask;
                file++;
                break;
            case 'n': 
                bitboards.bb_pieces[1][KNIGHT] |= mask;
                bitboards.bb_colors[1] |= mask;
                file++;
                break;
            case 'b': 
                bitboards.bb_pieces[1][BISHOP] |= mask;
                bitboards.bb_colors[1] |= mask;
                file++;
                break;
            case 'r': 
                bitboards.bb_pieces[1][ROOK] |= mask;
                bitboards.bb_colors[1] |= mask;
                file++;
                break;
            case 'q': 
                bitboards.bb_pieces[1][QUEEN] |= mask;
                bitboards.bb_colors[1] |= mask;
                file++;
                break;
            case 'k': 
                bitboards.bb_pieces[1][KING] |= mask;
                bitboards.bb_colors[1] |= mask;
                file++;
                break;
            case '/': 
                rank--;
                file = 0;
                break;
            default: 
                file += fen_pieces[i] - '0'; // conversion from char to int literal
        }
    }   
}

// Use previously parsed FEN string to set color to move
void get_turn_from_fen(std::string fen_turn, Board& bitboards){
    if(fen_turn == "w")
        bitboards.to_move = WHITE;
    else
        bitboards.to_move = BLACK;
}

// Use previously parsed FEN string to set castling rights
void get_castle_from_fen(std::string fen_castle, Board& bitboards){
    bitboards.st->castle = 0;
    for(char i : fen_castle){
        switch(i){
            case 'K':
                bitboards.st->castle |= WHITE_OO;
                break;
            case 'Q':
                bitboards.st->castle |= WHITE_OOO;
                break;
            case 'k':
                bitboards.st->castle |= BLACK_OO;
                break;
            case 'q':
                bitboards.st->castle |= BLACK_OOO;
                break;
            case '-':
                break;
        }
    }
}

// Use previously parsed FEN string to set en passant capture square, equal to the capturing pawn's destination square
void get_en_passant_from_fen(std::string fen_passant, Board& bitboards){
    if(fen_passant == "-"){
        bitboards.st->en_passant = 64;
    }
    else{
        fen_passant[0] = tolower(fen_passant[0]);
        bitboards.st->en_passant = algebraic_to_int(fen_passant);
    }
}

// Use previously parsed FEN string to set 50-move rule info and total moves
void get_moves_from_fen(std::string fen_halfmove, std::string fen_fullmove, Board& bitboards){
    bitboards.st->halfmove = std::stoi(fen_halfmove);
    bitboards.st->fullmove = std::stoi(fen_fullmove);
}

// Generates a Board from a FEN string, and set search tree root
Board get_board(std::string fen){
    Board board;

    board.root = BoardState{};
    board.st = &board.root;
    std::vector<std::string> fen_tokens = fen_parse(fen);
    get_bb_from_fen_pieces(fen_tokens[0], board);
    get_turn_from_fen(fen_tokens[1], board);
    get_castle_from_fen(fen_tokens[2], board);
    get_en_passant_from_fen(fen_tokens[3], board);
    get_moves_from_fen(fen_tokens[4], fen_tokens[5], board);

    
    return board;
}

// Convert an uint8_t to its corresponding square in algebraic notation
std::string int_to_algebraic(uint8_t integer){
    char file = 'a' + (integer % 8);
    char rank = '1' + (integer / 8);
    return std::string{file, rank};
}

// Convert algebraic notation to its corresponding uint8_t
uint8_t algebraic_to_int(std::string algebraic){
    return ((algebraic[0] - 'a') + ((algebraic[1] - '0') - 1) * 8);
}

// Generate a mask based on rank and file rather than uint8_t square
uint64_t get_mask(int rank, int file){ // start from 0 to 7 such that a1 = ((0 * 8) + 0) = 0 and h8 = ((7 * 8) + 7)
    uint64_t mask = 1ULL << ((rank * 8) + file);
    return mask;
}

// Get the file that a square is on
uint8_t get_file(uint8_t square){
    return square & 7; // square % 8
}

// Get the rank that a square is on
uint8_t get_rank(uint8_t square){
    return square >> 3; // square / 8
}

// Create a Move (uint16_t) using src square, dst square, and any flags. If flags contain a promotion, remember to add it: (PROMOTION | ((PIECE - 1) << 12)
Move set_move(uint8_t from, uint8_t to, uint16_t flags){ // store details about a move into a uint16_t (flags (4 bits) | to (6 bits) | from (6 bits))
    return flags | (to << 6) | from;
}

// Get the src square from a Move
uint8_t get_from_sq(Move move){
    return move & 0x3F;
}

// Get the dst square from a Move
uint8_t get_to_sq(Move move){
    return (move >> 6) & 0x3F;
}

// Get the promotion bits from a Move
uint8_t get_promo(Move move){
    return (move >> 12) & 0x3;
}

// Get the flag bits from a Move
uint8_t get_move_flags(Move move){
    return (move >> 14) & 0x3;
}

// Given a Move, returns the promotion piece. If not a promotion, return Pieces::NONE
uint8_t parse_promotion_flag(Move move){
    uint8_t flag = get_move_flags(move);
    if(flag != (PROMOTION >> 14)){
        return NONE;
    }
    else{
        uint8_t piece = get_promo(move);
        return piece + 1;
    }
}

// Check if a square on a bitboard is empty
uint8_t empty_square(uint8_t square, Board& board){
    Bitboard occupancy = board.bb_colors[0] | board.bb_colors[1];
    return ~((1ULL << square) & occupancy);
}

// Get the piece that is on a certain square, if any
uint8_t piece_on_square(Board& board, uint8_t color, uint8_t sq) {
    uint64_t m = 1ULL << sq;
    for (uint8_t pt = PAWN; pt <= KING; pt++)
        if (board.bb_pieces[color][pt] & m) return pt;
    return NONE;
}

// Debugging function that prints all the bitboards of a Board
void debug_bb(Board& board){
    std::string pieces[12] = {"w_pawn", "w_bishop", "w_knight", "w_rook", "w_queen", "w_king", 
        "b_pawn", "b_bishop", "b_knight", "b_rook", "b_queen", "b_king"};
    std::string colors[2] = {"white", "black"};

    std::cout << "Bitboards:\n\n";
    for(int color = 0; color < 2; color++){
        for(int piece = 0; piece < 6; piece++){
            std::cout << pieces[(color * 2) + piece] << "\n";
            print_bitboard(board.bb_pieces[color][piece]);
            std::cout << "------------------------\n";
        }
    }
    for(int color = 0; color < 2; color++){
        std::cout << colors[color] << "\n";
        print_bitboard(board.bb_colors[color]);
        std::cout << "------------------------\n";
    }
    std::cout << "all" << "\n";
    print_bitboard(board.bb_colors[0] | board.bb_colors[1]);
    std::cout << "------------------------\n";
}
