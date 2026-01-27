# Chess Engine with OpenGL

A modular chess engine with OpenGL visualization built with C++17. The project is structured for team collaboration with separate modules for engine logic, graphics rendering, and user interface.

## Project Structure

```
src/
├── engine/              # Chess game logic
│   ├── board.cpp/h         - Board representation using bitboards
│   ├── move_gen.cpp/h      - Move generation
│   └── constants.h         - Chess constants
│   └── move_gen.cpp/h      - Move generator
│
├── graphics/            # OpenGL rendering (SKELETON - TODO)
│   ├── renderer.cpp/h      - Window and OpenGL context management
│   └── shader.cpp/h        - Shader compilation and management
│
├── ui/                  # User interface (SKELETON - TODO)
│   └── board_view.cpp/h    - Chessboard visualization
│
└── main.cpp             # Entry point (SKELETON - TODO)
```

## Prerequisites

### 1. Install vcpkg (Package Manager)

**Clone vcpkg in your project directory:**
```bash
git clone https://github.com/microsoft/vcpkg.git vcpkg
cd vcpkg
```

**Bootstrap vcpkg:**

**Linux/WSL/macOS:**
```bash
./bootstrap-vcpkg.sh
```

### 2. Install System Dependencies

#### Linux/WSL (Ubuntu/Debian):
```bash
# Install all required dependencies in one command
sudo apt install build-essential cmake make pkg-config \
  mesa-common-dev libgl1-mesa-dev libglu1-mesa-dev \
  libxinerama-dev libxcursor-dev xorg-dev \
  curl zip unzip tar
```

#### macOS:
```bash
# Install CMake
brew install cmake

# Install Xcode Command Line Tools (C++ compiler + build tools)
xcode-select --install
```

## Setup Instructions

### Step 1: Configure the Project

**Option A: Using vcpkg in project directory (if you cloned vcpkg here):**
```bash
cmake -B build -S . -DCMAKE_TOOLCHAIN_FILE=./vcpkg/scripts/buildsystems/vcpkg.cmake
```

**Option B: Using vcpkg installed elsewhere:**
```bash
cmake -B build -S . -DCMAKE_TOOLCHAIN_FILE=<VCPKG_PATH>/scripts/buildsystems/vcpkg.cmake
```

This will:
- Download and install dependencies (GLFW, GLAD, OpenGL)
- Generate build files
- **First run takes 5-10 minutes** (downloads and builds libraries)

### Step 2: Build the Project

```
cmake --build build
```

### Step 3: Run the Program

**Linux/Mac:**
```bash
./build/chess
```

**Expected Output:**
- Console shows chess board and move list
- **No window will appear yet** (OpenGL rendering not implemented)

## Development Workflow

### Rebuilding After Changes

```bash
# Quick rebuild
cmake --build build

# Clean rebuild
cmake --build build --clean-first
```
