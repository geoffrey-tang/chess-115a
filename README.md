# Chess Engine

## Building & Running

**Build:**
```bash
make          # Compile the project
```

**Run:**
```bash
make run      # Build and run
./build/chess # Run directly
```

**Clean:**
```bash
make clean    # Remove build artifacts
make rebuild  # Clean and rebuild
```

## Testing

Modify the FEN string in [main.cpp](src/main.cpp) to test different positions:
- Starting position: `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1`
- En passant: `r1bqkbnr/ppp1pppp/n7/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3`
