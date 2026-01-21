#include <iostream>
#include <cstdint>
#include <string>
#include <vector>
#include <bitset>
#include "board.h"

void print_bitboard(Bitboard bitboard){
    for(int rank = 0; rank < 8; rank++){
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
    for(int rank = 0; rank < 8; rank++){
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

void generate_bb_from_fen_pieces(std::string fen_pieces, Board& bitboards){
    uint64_t pos = 0;
    for(int i = 0; i < fen_pieces.length(); i++){
        uint64_t mask = 1ULL << (LAST_BIT - pos);
        std::cout << fen_pieces[i] << " " << (LAST_BIT - pos) << " " << std::bitset<64>(mask) << "\n";
        //std::cout << fen_pieces[i];
        switch(fen_pieces[i]){
            case 'P': 
                bitboards.bb_pieces[0][PAWN] |= mask;
                bitboards.bb_colors[0] |= mask;
                pos++;
                break;
            case 'N': 
                bitboards.bb_pieces[0][KNIGHT] |= mask;
                bitboards.bb_colors[0] |= mask;
                pos++;
                break;
            case 'B': 
                bitboards.bb_pieces[0][BISHOP] |= mask;
                bitboards.bb_colors[0] |= mask;
                pos++;
                break;
            case 'R': 
                bitboards.bb_pieces[0][ROOK] |= mask;
                bitboards.bb_colors[0] |= mask;
                pos++;
                break;
            case 'Q': 
                bitboards.bb_pieces[0][QUEEN] |= mask;
                bitboards.bb_colors[0] |= mask;
                pos++;
                break;
            case 'K': 
                bitboards.bb_pieces[0][KING] |= mask;
                bitboards.bb_colors[0] |= mask;
                pos++;
                break;

            case 'p': 
                bitboards.bb_pieces[1][PAWN] |= mask;
                bitboards.bb_colors[1] |= mask;
                pos++;
                break;
            case 'n': 
                bitboards.bb_pieces[1][KNIGHT] |= mask;
                bitboards.bb_colors[1] |= mask;
                pos++;
                break;
            case 'b': 
                bitboards.bb_pieces[1][BISHOP] |= mask;
                bitboards.bb_colors[1] |= mask;
                pos++;
                break;
            case 'r': 
                bitboards.bb_pieces[1][ROOK] |= mask;
                bitboards.bb_colors[1] |= mask;
                pos++;
                break;
            case 'q': 
                bitboards.bb_pieces[1][QUEEN] |= mask;
                bitboards.bb_colors[1] |= mask;
                pos++;
                break;
            case 'k': 
                bitboards.bb_pieces[1][KING] |= mask;
                bitboards.bb_colors[1] |= mask;
                pos++;
                break;
            case '/': 
                break;
            default: 
                pos += fen_pieces[i] - '0'; // conversion from char to int literal
        }
    }   
}

uint64_t get_mask(int rank, int file){ // a = 0, b = 1, c = 2, d = 3, e = 4, f = 5, g = 6, h = 7
    uint64_t mask = 1ULL << (LAST_BIT - (rank * 8) - file);
    return mask;
}