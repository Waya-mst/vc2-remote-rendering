#version 330 core

#define POW2(X) ((X) * (X))

out vec4 output_color;

uniform sampler2D input_image;
uniform float luminance_average;
uniform float luminance_max;
uniform float key_value;

ivec2 group_num = ivec2($width, $height);

// Tone Mapping
vec4 toneMap(const in vec4 color) {
  float luminance = 0.27 * color.r + 0.67 * color.g + 0.06 * color.b;
  float luminance_fixed = key_value * (luminance / luminance_average);
  float luminance_max_fixed = key_value * (luminance_max / luminance_average);

  float luminance_mapped = luminance_fixed *
                           (1 + luminance_fixed / POW2(luminance_max_fixed)) /
                           (1 + luminance_fixed);

  vec3 color_fixed = color.rgb * (luminance_mapped / luminance);

  return vec4(clamp(color_fixed, 0, 1), 1.0f);
}

// Gamma Correction
vec4 gammaCorrect(const in vec4 color, const in float gamma) {
  float c = 1.0f / gamma;
  return vec4(pow(color.r, c), pow(color.g, c), pow(color.b, c), 1.0f);
}

void main() {
  vec4 color = texture(input_image, gl_FragCoord.xy / group_num.xy);
  color = toneMap(color);
  output_color = gammaCorrect(color, 2.2);
}
