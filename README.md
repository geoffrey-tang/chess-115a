# Chess Engine

A powerful chess engine with a beautiful Python GUI interface. Play chess against an intelligent AI opponent!

This project consists of two main parts:
- **C++ Chess Engine**: Fast, intelligent chess AI using bitboards and alpha-beta search
- **Python GUI**: Beautiful, user-friendly interface to play against the engine

### Getting Started

To play chess against the AI, you'll need to install both Python (for the GUI) and a C++ compiler (to build the chess engine).

#### **Step 1: Install Prerequisites**

**Python:**
- **Windows**: Download from [python.org](https://www.python.org/downloads/) (check "Add to PATH" during install)
- **macOS**: Run `brew install python3` (install [Homebrew](https://brew.sh/) first if needed)
- **Linux**: Run `sudo apt install python3 python3-pip python3-venv`

**C++ Compiler (needed to build the chess engine):**
- **Windows**: Install [MinGW-w64](https://www.mingw-w64.org/downloads/) or [Visual Studio](https://visualstudio.microsoft.com/) with C++ tools
- **macOS**: Run `xcode-select --install`
- **Linux**: Run `sudo apt install build-essential g++ make`

#### **Step 2: Build the Chess Engine**

The GUI needs the compiled chess engine to work. Build it with:

```bash
make
```

> **Note for Windows users:** If using MinGW, you may need to use `mingw32-make` instead of `make`

This creates `build/chess_cli` which the GUI uses for the AI opponent.

#### **Step 3: Set Up the GUI**

Open your terminal/command prompt in this folder and run:

**Windows (PowerShell):**
```powershell
cd gui_py
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS/Linux:**
```bash
cd gui_py
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### **Step 4: Run the Game**

```bash
python src/main.py
```

The chess GUI should open and you can start playing. 

---

## For Developers

### Building and Testing the Engine

Once you have the prerequisites installed (see Quick Start above), you can:

```bash
# Build the engine
make

# Run the engine in CLI mode (for direct UCI commands)
make run

# Clean build files
make clean

# Rebuild from scratch
make rebuild
```

The compiled engine will be in the `build/` folder as `chess_cli`.
