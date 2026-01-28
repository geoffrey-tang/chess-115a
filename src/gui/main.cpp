#include <iostream>
#include <cstdint>
#include <string>
#include <vector>
#include <bitset>

#include "board.h"
#include "move_gen.h"

#include "graphics/shader.h"
#include "graphics/renderer.h"

#include <glad/glad.h>
#include <GLFW/glfw3.h>


int width = 640;
int height = 480;

int main(void){
    Renderer renderer;
    
    if (!renderer.init(width, height, "Chess GUI")) {
        std::cerr << "Failed to initialize renderer" << std::endl;
        return -1;
    }
    
    // Main render loop
    while (!renderer.shouldClose()) {
        renderer.drawBoard();
        renderer.swapBuffers();
        glfwPollEvents();
    }
    
    return 0;
}