#include <iostream>
#include <cstdint>
#include <string>
#include <vector>
#include <bitset>
#include <iterator>
#include <algorithm>
#include "board.h"

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

void print_board(Board bitboards){
    char c;
    for(int rank = 7; rank >= 0; rank--){
        for(int file = 0; file < 8; file++){
            uint64_t mask = get_mask(rank, file);
            c = '+';
            for(int color = 0; color < 2; color++){
                for(int piece = 0; piece < 6; piece++){
                    if (bitboards.bb_pieces[color][piece] & mask){
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
    std::cout << (bitboards.white_to_move ? "White" : "Black") << " to move\n";
    std::cout << "Castling (W_OO, W_OOO, B_OO, B_OOO): " << std::bitset<4>(bitboards.castle) << "\n";
    std::cout << "En passant: " << (bitboards.en_passant != 64 ? int_to_algebraic(bitboards.en_passant) : "-") << "\n";
    std::cout << "50-move halfmove counter: " << bitboards.halfmove << "\n";
    std::cout << "Total moves: " << bitboards.fullmove << "\n";
}

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

void get_bb_from_fen_pieces(std::string fen_pieces, Board& bitboards){
    uint64_t file = 0;
    uint64_t rank = 7;
    for(int i = 0; i < fen_pieces.length(); i++){
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

void get_turn_from_fen(std::string fen_turn, Board& bitboards){
    if(fen_turn == "w")
        bitboards.white_to_move = true;
    else
        bitboards.white_to_move = false;
}

void get_castle_from_fen(std::string fen_castle, Board& bitboards){
    for(char i : fen_castle){
        switch(i){
            case 'K':
                bitboards.castle |= WHITE_OO;
                break;
            case 'Q':
                bitboards.castle |= WHITE_OOO;
                break;
            case 'k':
                bitboards.castle |= BLACK_OO;
                break;
            case 'q':
                bitboards.castle |= BLACK_OOO;
                break;
            case '-':
                break;
        }
    }
}

void get_en_passant_from_fen(std::string fen_passant, Board& bitboards){
    if(fen_passant == "-"){
        bitboards.en_passant = 64;
    }
    else{
        fen_passant[0] = tolower(fen_passant[0]);
        bitboards.en_passant = algebraic_to_int(fen_passant);
    }
}

void get_moves_from_fen(std::string fen_halfmove, std::string fen_fullmove, Board& bitboards){
    bitboards.halfmove = std::stoi(fen_halfmove);
    bitboards.fullmove = std::stoi(fen_fullmove);
}

Board get_board(std::string fen){
    Board board;
    std::vector<std::string> fen_tokens = fen_parse(fen);
    get_bb_from_fen_pieces(fen_tokens[0], board);
    get_turn_from_fen(fen_tokens[1], board);
    get_castle_from_fen(fen_tokens[2], board);
    get_en_passant_from_fen(fen_tokens[3], board);
    get_moves_from_fen(fen_tokens[4], fen_tokens[5], board);
    return board;
}

std::string int_to_algebraic(uint8_t integer){
    uint8_t rank;
    for(uint8_t i = 0; i < 8; i++){
        if( (i * 8) > integer){
            rank = i;
            break;
        }
    }
    char file = 'a' + (integer - ((rank - 1) * 8));
    std::string square = file + std::to_string(rank);
    return square;
}

uint8_t algebraic_to_int(std::string algebraic){
    return ((algebraic[0] - 'a') + ((algebraic[1] - '0') - 1) * 8);
}

uint64_t get_mask(int rank, int file){ // start from 0 to 7 such that a1 = ((0 * 8) + 0) = 0
    uint64_t mask = 1ULL << ((rank * 8) + file);
    return mask;
}

uint8_t get_file(uint8_t square){
    return square & 7; // square % 8
}

uint8_t get_rank(uint8_t square){
    return square >> 3; // square / 8
}

uint8_t empty_square(uint8_t square, Board& board){
    Bitboard occupancy = board.bb_colors[0] | board.bb_colors[1];
    return ~((1ULL << square) & occupancy);
}
