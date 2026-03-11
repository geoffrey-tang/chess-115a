#include "uci.h"

#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <cassert>
#include <chrono>
#include <cmath>

#include "board.h"
#include "move_gen.h"
#include "constants.h"
#include "search.h"
#include "zobrist.h"
#include "time_man.h"

static const char* ENGINE_NAME = "chess-115a";
static const char* ENGINE_AUTHOR = "Team";

// start position FEN pretty standard but we can change
static const std::string STARTPOS_FEN =
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

static std::vector<std::string> split_ws(const std::string& s) {
    std::istringstream iss(s);
    std::vector<std::string> out;
    std::string t;

    while (iss >> t){
        out.push_back(t);
    }

    return out;
}

static SearchLimits parse_go(const std::vector<std::string>& tok) {
    SearchLimits lim;

    for (size_t i = 1; i < tok.size(); i++) {
        if (tok[i] == "movetime") {
            if (i + 1 < tok.size()) {
                lim.movetime = std::stoi(tok[i + 1]);
            }
            continue;
        }
        if (tok[i] == "depth") {
            if (i + 1 < tok.size()) {
                lim.depth = std::stoi(tok[i + 1]);
            }
            continue;
        }
        if (tok[i] == "wtime") {
            if (i + 1 < tok.size()) {
                lim.wtime = std::stoi(tok[i + 1]);
            }
            continue;
        }
        if (tok[i] == "btime") {
            if (i + 1 < tok.size()) {
                lim.btime = std::stoi(tok[i + 1]);
            }
            continue;
        }
        if (tok[i] == "winc") {
            if (i + 1 < tok.size()) {
                lim.winc = std::stoi(tok[i + 1]);
            }
            continue;
        }
        if (tok[i] == "binc") {
            if (i + 1 < tok.size()) {
                lim.binc = std::stoi(tok[i + 1]);
            }
            continue;
        }
    }
    return lim;
}

std::string move_to_uci(Move m) {
    std::string s = int_to_algebraic(get_from_sq(m)) + int_to_algebraic(get_to_sq(m));
    uint8_t pp = parse_promotion_flag(m); // returns KNIGHT/BISHOP/ROOK/QUEEN or NONE
    if (pp != NONE) {
        char c = 'q';
        if (pp == KNIGHT) c = 'n';
        else if (pp == BISHOP) c = 'b';
        else if (pp == ROOK) c = 'r';
        else if (pp == QUEEN) c = 'q';
        s.push_back(c);
    }
    return s;
}

Move uci_to_move(Board& b, StateStack& ss, std::string uci){
    for(Move m : generate_moves(b, ss)){
        if(move_to_uci(m) == uci){
            return m;
        }
    }
    return 0;
}

static void set_position(const std::vector<std::string>& tok, Board& board, StateStack& ss){
    // "position startpos"
    // "position fen <6 fields>"
    if (tok.size() < 2) return;

    size_t i = 1;
    if (tok[i] == "startpos") {
        board = get_board(STARTPOS_FEN);
        init_state_stack(board, ss);
        i++;
    } else if (tok[i] == "fen") {
        if (tok.size() < i + 1 + 6) return;
        std::string fen;
        for (int k = 0; k < 6; k++) {
            if (k) fen += " ";
            fen += tok[i + 1 + k];
        }
        board = get_board(fen);
        init_state_stack(board, ss);
        i += 1 + 6;
    } else {
        return;
    }

    if (i < tok.size() && tok[i] == "moves"){
        i++;
        for(; i < tok.size(); i++){
            Move m = uci_to_move(board, ss, tok[i]);
            if(m == 0) break; // break when illegal move played
            do_move(board, ss, m);
        }
    }
    // "moves ..." requires make_move() User Story 1 task 1
    // when we have make_move(board, move), apply them here.
    // if (i < tok.size() && tok[i] == "moves") { ... }
}

int run_uci_loop() {

    StateStack ss;
    Board board = get_board(STARTPOS_FEN);
    BoardState* new_st = init_state_stack(board, ss);
    StGuard guard(board, new_st);
    TranspositionTable tt;
    TimeManager tm;
    tt.resize_mb(256);

    std::string line;
    while (std::getline(std::cin, line)) {
        auto tok = split_ws(line);
        if (tok.empty()) continue;

        const std::string& cmd = tok[0];

        if (cmd == "uci") {
            std::cout << "id name " << ENGINE_NAME << "\n";
            std::cout << "id author " << ENGINE_AUTHOR << "\n";
            std::cout << "uciok\n";
        }
        else if (cmd == "isready") {
            std::cout << "readyok\n";
        }
        else if (cmd == "ucinewgame") {
            board = get_board(STARTPOS_FEN);
            init_state_stack(board, ss);
        }
        else if (cmd == "position") {
            set_position(tok, board, ss);
        }
        else if (cmd == "go") {
            SearchLimits limits = parse_go(tok);
            TimeManager time_man;
            if(limits.movetime >= 0){
                time_man.init_movetime(limits.movetime);
            }
            else if(limits.wtime >= 0 && limits.btime >= 0) {
                time_man.init_clock(board.to_move == WHITE ? limits.wtime : limits.btime, 
                                    board.to_move == WHITE ? limits.winc : limits.binc);
            }
            else{
                time_man.init_depth();
            }

            SearchStats stats{};
            auto start = std::chrono::steady_clock::now();
            time_man.start_clock();
            SearchResult r = iter_deepening(board, tt, stats, time_man, limits.depth);
            auto end = std::chrono::steady_clock::now();
            auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
            uint64_t nps = (ms > 0) ? (stats.nodes * 1000ULL) / ms : 0;

            // r.score_cp is from side to move perspective (negamax)
            // UCI usually expects score from side to move so its fine
            std::cout 
                << "info depth " << stats.depth  
                << " seldepth " << stats.seldepth 
                << " nodes " << stats.nodes
                << " time " << ms
                << " nps " << nps
                << " score cp " << r.score_cp << "\n";

            if (r.best_move == 0) {
                std::cout << "bestmove 0000\n";
            } else {
                std::cout << "bestmove " << move_to_uci(r.best_move) << "\n";
            }
        }
        else if (cmd == "d"){
            print_board(board);
        }
        else if (cmd == "perft"){
            SearchLimits limits = parse_go(tok);
            perft_divide(board, limits.depth);
        }
        else if (cmd == "quit") {
            break;
        }
        else {
            // ignore: setoption, stop
        }
    }

    return 0;
}

