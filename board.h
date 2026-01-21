#include <iostream>
#include <cstdint>
#include <string>
#include <vector>
#include <bitset>

#define LAST_BIT 63

void print_bitboard(uint64_t bitboard){
    for(int rank = 0; rank < 8; rank++){
        for(int file = 0; file < 8; file++){
            uint64_t mask = 1ULL << (LAST_BIT - (rank * 8) - file);
            char c = (bitboard & mask) ? '1' : '0';
            std::cout << c << ' ';
        }
        std::cout << '\n';
    }
}

void print_board(uint64_t* bitboards){
    char c;
    for(int rank = 0; rank < 8; rank++){
        for(int file = 0; file < 8; file++){
            uint64_t mask = 1ULL << (LAST_BIT - (rank * 8) - file);
            c = '+';
            for(int i = 0; i < 12; i++){
                if (bitboards[i] & mask){
                    switch(i){
                        case 0:
                            c = 'P';
                            break;
                        case 1:
                            c = 'B';
                            break;
                        case 2:
                            c = 'N';
                            break;
                        case 3:
                            c = 'R';
                            break;
                        case 4:
                            c = 'Q';
                            break;
                        case 5:
                            c = 'K';
                            break;
                        case 6:
                            c = 'p';
                            break;
                        case 7:
                            c = 'b';
                            break;
                        case 8:
                            c = 'n';
                            break;
                        case 9:
                            c = 'r';
                            break;
                        case 10:
                            c = 'q';
                            break;
                        case 11:
                            c = 'k';
                            break;
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

void generate_bb_fen_pieces(std::string fen_pieces, uint64_t* bb_array){ // Use the first part of the parsed FEN string 
    uint64_t pos = 0;
    for(int i = 0; i < fen_pieces.length(); i++){
        uint64_t mask = 1ULL << (LAST_BIT - pos);
        //std::cout << fen_pieces[i] << " " << (LAST_BIT - pos) << " " << std::bitset<64>(mask) << "\n";
        //std::cout << fen_pieces[i];
        switch(fen_pieces[i]){
            case 'P': 
                bb_array[0] |= mask;
                pos++;
                break;
            case 'B': 
                bb_array[1] |= mask; 
                pos++;
                break;
            case 'N': 
                bb_array[2] |= mask; 
                pos++;
                break;
            case 'R': 
                bb_array[3] |= mask; 
                pos++;
                break;
            case 'Q': 
                bb_array[4] |= mask; 
                pos++;
                break;
            case 'K': 
                bb_array[5] |= mask; 
                pos++;
                break;

            case 'p': 
                bb_array[6] |= mask; 
                pos++;
                break;
            case 'b': 
                bb_array[7] |= mask; 
                pos++;
                break;
            case 'n': 
                bb_array[8] |= mask; 
                pos++;
                break;
            case 'r': 
                bb_array[9] |= mask; 
                pos++;
                break;
            case 'q': 
                bb_array[10] |= mask; 
                pos++;
                break;
            case 'k': 
                bb_array[11] |= mask; 
                pos++;
                break;
            case '/': 
                break;
            default: 
                pos += fen_pieces[i] - '0'; // conversion from char to int literal
        }
    }   
}