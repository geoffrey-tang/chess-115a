#include "search.h"
#include "board.h"
#include "move_gen.h"
#include "constants.h"

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