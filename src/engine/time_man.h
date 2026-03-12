#pragma once

#include <chrono>
#include <stdio.h>

// Time manager that ensures that engine will not get stuck in an exploding search
struct TimeManager {
    int soft_limit_ms = 0; // used at iterative deepening to see if we want to try the next depth
    int hard_limit_ms = 0; // hard cutoff to kill a search mid-search
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

    // Initializes limits for "go" if wtime and btime are supplied
    void init_clock(int time_left_ms, int increment_ms, int moves_to_go = 40) {
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

    // Initializes limits for "go movetime"
    void init_movetime(int movetime_ms) {
        int safe = std::max(1, movetime_ms);
        
        soft_limit_ms = std::max(1, safe * 8 / 10);
        hard_limit_ms = safe;

        use_soft_limit = true;
        use_hard_limit = true;
    }

    // Iniializes limits for "go depth" without wtime or btime
    void init_depth(int emergency_ms = 10000) {
        soft_limit_ms = 0;
        hard_limit_ms = std::max(1, emergency_ms);

        use_soft_limit = false;
        use_hard_limit = true;
    }

    // Check if limits are reached
    bool soft_expired() { return use_soft_limit && elapsed_ms() >= soft_limit_ms; }
    bool hard_expired() { return use_hard_limit && elapsed_ms() >= hard_limit_ms; }
};