# Compiler and flags
CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -g -O2
LDFLAGS = 

# Directories
SRC_DIR = src
ENGINE_DIR = $(SRC_DIR)/engine
BUILD_DIR = build

# Engine CLI sources (GUI uses CMake)
ENGINE_SOURCES = $(ENGINE_DIR)/board.cpp $(ENGINE_DIR)/move_gen.cpp $(ENGINE_DIR)/uci.cpp $(ENGINE_DIR)/main.cpp $(ENGINE_DIR)/eval.cpp $(ENGINE_DIR)/search.cpp

ENGINE_OBJECTS = $(patsubst $(ENGINE_DIR)/%.cpp,$(BUILD_DIR)/%.o,$(ENGINE_SOURCES))

# CLI executable target
TARGET = $(BUILD_DIR)/chess_cli

# Default target
all: $(TARGET)

# Link CLI executable
$(TARGET): $(ENGINE_OBJECTS) | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(ENGINE_OBJECTS) -o $(TARGET) $(LDFLAGS)
	@echo Build complete: $(TARGET)

# Compile engine sources
$(BUILD_DIR)/%.o: $(ENGINE_DIR)/%.cpp | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -I$(ENGINE_DIR) -c $< -o $@

# Create build directory if it doesn't exist
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Run the CLI engine
run: $(TARGET)
	./$(TARGET)

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR)
	@echo Clean complete

# Rebuild everything
rebuild: clean all

.PHONY: all clean run rebuild
