#include <limits>
#include "search.h"
#include "board.h"
#include "move_gen.h"
#include "constants.h"
#include "eval.h"
#include "uci.h"

void init_state_stack(Board& board, StateStack& ss){
    ss.ply = 0;
    ss.states[0] = board.root;
    ss.states[0].previous = nullptr;
    board.st = &ss.states[0];
}

uint64_t perft(Board& b, StateStack& ss, int depth){
    if(depth == 0) return 1;
    uint64_t nodes = 0;
    std::vector<Move> moves = generate_moves(b, ss);

    for(Move m : moves){
        do_move(b, ss, m);
        nodes += perft(b, ss, depth - 1);
        undo_move(b, ss, m);
    }
    return nodes;
}

uint64_t perft_divide(Board& b, int depth){
    StateStack ss;
    init_state_stack(b, ss);
    uint64_t total = 0;
    std::vector<Move> moves = generate_moves(b, ss);
    
    std::cout << "perft_divide at depth " << depth << std::endl;
    for (Move m : moves) {
        do_move(b, ss, m);
        uint64_t nodes = perft(b, ss, depth - 1);
        undo_move(b, ss, m);

        std::cout << move_to_uci(m) << ": " << nodes << "\n";
        total += nodes;
    }

    std::cout << "\nNodes searched: " << total << "\n";
    return total;
}

Move search(Board &b, int depth){
    StateStack ss;
    init_state_stack(b, ss);
    int max = -1 * std::numeric_limits<int>::max();
    Move best_move = 0;
    std::vector<Move> moves = generate_moves(b, ss);
    for(Move m : moves) {
        do_move(b, ss, m);
        int score = -1 * negamax(b, ss, depth - 1);
        if(score > max){
            max = score;
            best_move = m;
        }
        undo_move(b, ss, m);
    }
    return best_move;
}

int negamax(Board& b, StateStack& ss, int depth){
    if(depth == 0) return material_score(b); // change this to eval when proper eval is implemented
    int max = -1 * std::numeric_limits<int>::max();
    std::vector<Move> moves = generate_moves(b, ss);

    // check/stale mate check
    if(moves.empty()){
        uint8_t color = b.to_move;
        bool in_check = square_attacked(b, king_square(b, color), !color);
        if(in_check)
            return -1 * std::numeric_limits<int>::max();
        else
            return 0;
    }
    
    for(Move m : moves){
        do_move(b, ss, m);
        int score = -1 * negamax(b, ss, depth - 1);
        if(score > max) max = score;
        undo_move(b, ss, m);
    }
    return max;
}