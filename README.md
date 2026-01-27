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

**Linux/WSL:**
```bash
./bootstrap-vcpkg.sh
```

**macOS:**
```bash
./bootstrap-vcpkg.sh
```

**Windows:**
```powershell
.\bootstrap-vcpkg.bat
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

#### Windows:
**Option A: Visual Studio (Recommended)**
1. Install [Visual Studio 2019 or later](https://visualstudio.microsoft.com/downloads/) (Community Edition is free)
   - During installation, select "Desktop development with C++"
   - This includes CMake, C++ compiler, and Windows SDK
2. OpenGL support is included with Windows SDK

**Option B: MinGW-w64 + CMake**
1. Install [CMake for Windows](https://cmake.org/download/)
2. Install [MinGW-w64](https://www.mingw-w64.org/downloads/)
3. Add MinGW bin directory to PATH

**Option C: WSL (Windows Subsystem for Linux)**
Follow the Linux/WSL instructions above after [installing WSL](https://learn.microsoft.com/en-us/windows/wsl/install).

## Setup Instructions

### Step 1: Configure the Project

**Linux/WSL/macOS:**
```bash
cmake -B build -S . -DCMAKE_TOOLCHAIN_FILE=./vcpkg/scripts/buildsystems/vcpkg.cmake
```

**Windows (PowerShell):**
```powershell
cmake -B build -S . -DCMAKE_TOOLCHAIN_FILE=./vcpkg/scripts/buildsystems/vcpkg.cmake
```

**Windows (Visual Studio):**
```powershell
cmake -B build -S . -DCMAKE_TOOLCHAIN_FILE=./vcpkg/scripts/buildsystems/vcpkg.cmake -G "Visual Studio 17 2022"
```
*Note: Use "Visual Studio 16 2019" if you have VS 2019*

This will:
- Download and install dependencies (GLFW, GLAD, OpenGL)
- Generate build files
- **First run takes 5-10 minutes** (downloads and builds libraries)

### Step 2: Build the Project

**Linux/WSL/macOS:**
```bash
cmake --build build
```

**Windows (Command Line):**
```powershell
cmake --build build --config Release
```

**Windows (Visual Studio):**
Open `build/chess-115a.sln` in Visual Studio and press F5 to build and run.

### Step 3: Run the Program

**Linux/WSL/macOS:**
```bash
./build/chess
```

**Windows (Command Line):**
```powershell
# If using Visual Studio generator:
.\build\Release\chess.exe

# If using MinGW/Unix Makefiles generator:
.\build\chess.exe
```

## Development Workflow

### Rebuilding After Changes

```bash
# Quick rebuild
cmake --build build

# Clean rebuild
cmake --build build --clean-first
```
