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
    while (iss >> t) out.push_back(t);
    return out;
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

static void set_position(const std::vector<std::string>& tok, Board& board) {
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

    // "moves ..." requires make_move() User Story 1 task 1
    // when we have make_move(board, move), apply them here.
    // if (i < tok.size() && tok[i] == "moves") { ... }
}

int run_uci_loop() {

    Board board = get_board(STARTPOS_FEN);

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
            set_position(tok, board);
        }
        else if (cmd == "go") {
            // temp: choose first generated move so UCI basics work now.
            // later add this into minimax/search.
            StateStack ss;
            init_state_stack(board, ss);
            std::vector<Move> moves = generate_moves(board, ss);
            if (moves.empty()) {
                std::cout << "bestmove 0000\n";
            } else {
                std::cout << "bestmove " << move_to_uci(moves[0]) << "\n";
            }
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

