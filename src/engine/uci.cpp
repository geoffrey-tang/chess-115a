#include "uci.h"

#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "board.h"
#include "move_gen.h"
#include "constants.h"
#include "search.h"

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

static int parse_go_depth(const std::vector<std::string>& tok) {
    int depth = 5;

    for (size_t i = 1; i < tok.size(); i++) {
        if (tok[i] == "depth") {
            if (i + 1 < tok.size()) {
                depth = std::stoi(tok[i + 1]);
            }
            break;
        }
    }

    return depth;
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
        i++;
    } else if (tok[i] == "fen") {
        if (tok.size() < i + 1 + 6) return;
        std::string fen;
        for (int k = 0; k < 6; k++) {
            if (k) fen += " ";
            fen += tok[i + 1 + k];
        }
        board = get_board(fen);
        i += 1 + 6;
    } else {
        return;
    }

    if (i < tok.size() && tok[i] == "moves"){
        i++;
        for(; i < tok.size(); i++){
            Move m = uci_to_move(board, ss, tok[i]);
            if(m == 0) break;
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
    init_state_stack(board, ss);

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
        }
        else if (cmd == "position") {
            init_state_stack(board, ss);
            set_position(tok, board, ss);
        }
        else if (cmd == "go") {
            int depth = parse_go_depth(tok);
            SearchResult r = search_root(board, depth);

            // r.score_cp is from side to move perspective (negamax)
            // UCI usually expects score from side to move so its fine
            std::cout << "info depth " << depth << " score cp " << r.score_cp << "\n";

            if (r.best_move == 0) {
                std::cout << "bestmove 0000\n";
            } else {
                std::cout << "bestmove " << move_to_uci(r.best_move) << "\n";
            }
        }
        else if (cmd == "d"){
            print_board(board);
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

