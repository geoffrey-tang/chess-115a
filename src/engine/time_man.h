#pragma once

#include <chrono>
#include <stdio.h>

struct TimeManager {
    int soft_limit_ms = 0;
    int hard_limit_ms = 0;
    bool use_soft_limit = true;
    bool use_hard_limit = true;
    std::chrono::steady_clock::time_point start;

    void start_clock(){
        start = std::chrono::steady_clock::now();
    }

    int elapsed_ms(){
        using namespace std::chrono;
        return (int)duration_cast<milliseconds>(steady_clock::now() - start).count();
    }

    void init_clock(int time_left_ms, int increment_ms, int moves_to_go = 40) { // if wtime and btime are supplied
        int safe = std::max(1, time_left_ms);

        int mtg = moves_to_go > 0 ? moves_to_go : 40;
        int base = safe / mtg;
        int bonus = increment_ms /2;

        soft_limit_ms = base + bonus;
        soft_limit_ms = std::max(1, soft_limit_ms);

        hard_limit_ms = std::min(soft_limit_ms * 3, safe / 4);
        hard_limit_ms = std::max(soft_limit_ms, hard_limit_ms);
        
        use_soft_limit = true;
        use_hard_limit = true;
    }

    void init_movetime(int movetime_ms) { // go movetime
        int safe = std::max(1, movetime_ms);
        
        soft_limit_ms = std::max(1, safe * 8 / 10);
        hard_limit_ms = safe;

        use_soft_limit = true;
        use_hard_limit = true;
    }

    void init_depth(int emergency_ms = 10000) { // go depth, no wtime/btime supplied
        soft_limit_ms = 0;
        hard_limit_ms = std::max(1, emergency_ms);

        use_soft_limit = false;
        use_hard_limit = true;
    }

    bool soft_expired() { return use_soft_limit && elapsed_ms() >= soft_limit_ms; }
    bool hard_expired() { return use_hard_limit && elapsed_ms() >= hard_limit_ms; }
};