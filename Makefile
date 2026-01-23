# Compiler and flags
CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -g -O2
LDFLAGS = 

# Directories
SRC_DIR = src
BUILD_DIR = build

# Source files
SOURCES = $(SRC_DIR)/main.cpp $(SRC_DIR)/board.cpp $(SRC_DIR)/move_gen.cpp
OBJECTS = $(patsubst $(SRC_DIR)/%.cpp,$(BUILD_DIR)/%.o,$(SOURCES))

# Output executable
TARGET = $(BUILD_DIR)/chess

# Default target
all: $(TARGET)

# Link the executable
$(TARGET): $(OBJECTS) | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(OBJECTS) -o $(TARGET) $(LDFLAGS)
	@echo Build complete: $(TARGET)

# Compile source files
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Create build directory if it doesn't exist
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Run the program
run: $(TARGET)
	./$(TARGET)

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR)
	@echo Clean complete

# Rebuild everything
rebuild: clean all

.PHONY: all clean run rebuild
