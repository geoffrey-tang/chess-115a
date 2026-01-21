#include <iostream>
#include <cstdint>
#include <string>
#include <vector>

void print_bitboard(uint64_t bitboard){
    const uint64_t last_bit = 63;
    for(int rank = 0; rank < 8; rank++){
        for(int file = 0; file < 8; file++){
            uint64_t mask = 1ULL << (last_bit - (rank * 8) - file);
            char c = (bitboard & mask) ? '1' : '0';
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

int main(){
    std::string fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"; // add fen strings to bitboards next
    uint64_t bitboards[12] = {
        0b0000000000000000000000000000000000000000000000001111111100000000,
        0b0000000000000000000000000000000000000000000000000000000000100100,
        0b0000000000000000000000000000000000000000000000000000000001000010,
        0b0000000000000000000000000000000000000000000000000000000010000001,
        0b0000000000000000000000000000000000000000000000000000000000010000,
        0b0000000000000000000000000000000000000000000000000000000000001000,
        0b0000000011111111000000000000000000000000000000000000000000000000,
        0b0010010000000000000000000000000000000000000000000000000000000000,
        0b0100001000000000000000000000000000000000000000000000000000000000,
        0b1000000100000000000000000000000000000000000000000000000000000000,
        0b0001000000000000000000000000000000000000000000000000000000000000,
        0b0000100000000000000000000000000000000000000000000000000000000000
    };
    /*
    0 = white pawn
    1 = white bishop
    2 = white knight
    3 = white rook
    4 = white queen
    5 = white king
    6 = black pawn
    7 = black bishop
    8 = black knight
    9 = black rook
    10 = black queen
    11 = black king
    */
    bool turn = 0; //0 = white, 1 = black    
    for(uint64_t board : bitboards){
        print_bitboard(board);
        std::cout << "------------------------\n";
    }
    std::vector<std::string> fen_tokens = fen_parse(fen);
    std::cout << "FEN parse elements:\n";
    for (const auto& element : fen_tokens) {
        std::cout << element << "\n";
    }
    return 0;
}