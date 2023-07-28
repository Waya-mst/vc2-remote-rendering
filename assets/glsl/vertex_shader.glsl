#version 430 core

in vec2 position_vertices;

void main() { gl_Position = vec4(position_vertices, 0.0f, 1.0f); }
