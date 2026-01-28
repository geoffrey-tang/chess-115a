#pragma once
#include <iostream>
#include <string>
#include <fstream>
#include <sstream>

#include <glad/glad.h>
#include <GLFW/glfw3.h>

struct ShaderProgramSource{
    std::string VertexSource;
    std::string FragmentSource;
};

unsigned int CreateShader(const std::string& vertexShader, const std::string& fragmentShader); 

unsigned int CompileShader(const std::string& source, unsigned int type);

ShaderProgramSource ParseShader(const std::string& filepath);