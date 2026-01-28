#ifndef RENDERER_H
#define RENDERER_H

#include "shader.h"
#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include <string>

class Renderer {
public:
    Renderer();
    ~Renderer();

    // Initialize window and OpenGL
    bool init(int width, int height, const char* title);
    
    // The main drawing command
    void drawBoard();

    // Utility
    bool shouldClose();
    void swapBuffers();

private:
    GLFWwindow* window;
    unsigned int shaderProgram;
    unsigned int VAO, VBO, EBO;

    // Internal helper to compile shaders
    unsigned int compileShaders(const std::string& vertexSource, const std::string& fragmentSource);
};

#endif