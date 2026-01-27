cmake_minimum_required(VERSION 3.20)

project(chess-115a VERSION 0.1.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Export compile commands for better IDE integration
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Find OpenGL and related dependencies
find_package(OpenGL REQUIRED)
find_package(glfw3 CONFIG REQUIRED)
find_package(glad CONFIG REQUIRED)

# Engine sources (chess logic)
set(ENGINE_SOURCES
    src/engine/board.cpp
    src/engine/move_gen.cpp
)

set(ENGINE_HEADERS
    src/engine/board.h
    src/engine/move_gen.h
    src/engine/constants.h
)

# Graphics sources (OpenGL rendering)
set(GRAPHICS_SOURCES
    # src/graphics/renderer.cpp
    # src/graphics/shader.cpp
)

set(GRAPHICS_HEADERS
    # src/graphics/renderer.h
    # src/graphics/shader.h
)

# UI sources (interface)
set(UI_SOURCES
    # src/ui/board_view.cpp
)

set(UI_HEADERS
    # src/ui/board_view.h
)

# Main entry point
set(MAIN_SOURCES
    src/main.cpp
)

# Combine all sources
set(ALL_SOURCES
    ${MAIN_SOURCES}
    ${ENGINE_SOURCES}
    ${GRAPHICS_SOURCES}
    ${UI_SOURCES}
)

set(ALL_HEADERS
    ${ENGINE_HEADERS}
    ${GRAPHICS_HEADERS}
    ${UI_HEADERS}
)

# Create executable
add_executable(chess ${ALL_SOURCES} ${ALL_HEADERS})

# Link OpenGL libraries
target_link_libraries(chess PRIVATE
    OpenGL::GL
    glfw
    glad::glad
)

# Include directories for each module
target_include_directories(chess PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}/src/engine
    ${CMAKE_CURRENT_SOURCE_DIR}/src/graphics
    ${CMAKE_CURRENT_SOURCE_DIR}/src/ui
)

# Compiler warnings
if(MSVC)
    target_compile_options(chess PRIVATE /W4)
else()
    target_compile_options(chess PRIVATE -Wall -Wextra -O2)
endif()

# Add optimization flag for Release builds
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    if(MSVC)
        target_compile_options(chess PRIVATE /O2)
    else()
        target_compile_options(chess PRIVATE -O3)
    endif()
endif()
