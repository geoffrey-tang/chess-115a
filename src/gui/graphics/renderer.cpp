#include "renderer.h"
#include "shader.h"
#include <iostream>

Renderer::Renderer() : window(nullptr), shaderProgram(0) {}

bool Renderer::init(int width, int height, const char* title) {
    if (!glfwInit()) return false;

    window = glfwCreateWindow(width, height, title, NULL, NULL);
    if (!window) return false;

    glfwMakeContextCurrent(window);
    gladLoadGLLoader((GLADloadproc)glfwGetProcAddress);

    // 1. Setup Geometry
    float vertices[] = { 0.125f, 0.125f, 0.0f, 0.125f, -0.125f, 0.0f, -0.125f, -0.125f, 0.0f, -0.125f, 0.125f, 0.0f };
    unsigned int indices[] = { 0, 1, 3, 1, 2, 3 };

    //VAO (Vertex Array Object) - stores configuration of how to read vertex data
    glGenVertexArrays(1, &VAO);
    //VBO (Vertex Buffer Object) - stores vertex positions in GPU memory
    glGenBuffers(1, &VBO);
    //EBO (Element Buffer Object) - stores indices in GPU memory
    glGenBuffers(1, &EBO);

    //Activates the VAO - all subsequent setup is recorded in it
    glBindVertexArray(VAO);

    //Binds VBO and uploads vertex data to GPU
    glBindBuffer(GL_ARRAY_BUFFER, VBO);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);
    
    //Binds EBO and uploads index data to GPU
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(indices), indices, GL_STATIC_DRAW);

    //Tells OpenGL how to interpret the vertex data
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * sizeof(float), (void*)0);
    //Enables vertex attribute 0 (position)
    glEnableVertexAttribArray(0);

    // 2. Setup Shaders
    ShaderProgramSource source = ParseShader("src/gui/graphics/res/shaders/Basic.shader");
    std::cout << "VERTEX" << std::endl;
    std::cout << source.VertexSource << std::endl;
    std::cout << "FRAGMENT" << std::endl;
    std::cout << source.FragmentSource << std::endl;

    shaderProgram = CreateShader(source.VertexSource, source.FragmentSource);
    if (shaderProgram == 0) {
        std::cerr << "Failed to create shader program" << std::endl;
        return false;
    }

    std::cout << "OpenGL initialized successfully" << std::endl;
    return true; 
}

Renderer::~Renderer() {
    if (VAO) glDeleteVertexArrays(1, &VAO);
    if (VBO) glDeleteBuffers(1, &VBO);
    if (EBO) glDeleteBuffers(1, &EBO);
    if (shaderProgram) glDeleteProgram(shaderProgram);
    if (window) {
        glfwDestroyWindow(window);
        glfwTerminate();
    }
}

void Renderer::drawBoard() {
    //Clears the screen (black background)
    glClear(GL_COLOR_BUFFER_BIT);
    //Activates your shader program
    glUseProgram(shaderProgram);
    //Activates the square geometry
    glBindVertexArray(VAO);

    //Loops through 64 chessboard squares
    for (int y = 0; y < 8; y++) {
        for (int x = 0; x < 8; x++) {
            float xOffset = -0.875f + (x * 0.25f);
            float yOffset = -0.875f + (y * 0.25f);
            
            glUniform2f(glGetUniformLocation(shaderProgram, "offset"), xOffset, yOffset);
            glUniform1i(glGetUniformLocation(shaderProgram, "isDark"), (x + y) % 2);
            
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, 0);
        }
    }
}

bool Renderer::shouldClose() {
    return glfwWindowShouldClose(window);
}

void Renderer::swapBuffers() {
    glfwSwapBuffers(window);
}