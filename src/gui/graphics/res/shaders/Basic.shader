#shader vertex
#version 330 core
layout (location = 0) in vec3 aPos;
uniform vec2 offset; // The position of the square on the grid

void main() {
    // Each square is 1/8th of the board (0.25 in NDC if the board is 2.0 wide)
    gl_Position = vec4(aPos.x + offset.x, aPos.y + offset.y, aPos.z, 1.0);
}

#shader fragment
#version 330 core
out vec4 FragColor;
uniform bool isDark;

void main() {
    if (isDark)
        FragColor = vec4(0.45, 0.31, 0.22, 1.0); // Brown
    else
        FragColor = vec4(0.94, 0.85, 0.71, 1.0); // Tan
}
