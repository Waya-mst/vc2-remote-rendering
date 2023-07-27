#version 430 core

#define POW2(X) ((X) * (X))
#define POW5(X) ((X) * (X) * (X) * (X) * (X))
#define DEPTH_MAX (16)
#define SAMPLE_MAX ($sample_max)
#define DELTA (0.01)
#define PI (3.14159265359)

#define BACKGROUND (0)
#define DIFFUSE (1)
#define MIRROR (2)
#define GLASS (3)

in vec2 position_screen;
out vec4 output_color;

layout(binding = 1, rgba32f) uniform image2D input_image;
layout(binding = 2, rgba32ui) uniform uimage2D seed_image;
layout(binding = 3) uniform sampler2D background_image;

uniform int current_sample;
uniform float theta;
uniform float phi;
uniform float move_x;
uniform float move_y;

ivec2 group_num = ivec2($width, $height);
ivec2 group_idx = ivec2(gl_FragCoord.x, gl_FragCoord.y);

struct Ray {
  vec3 origin;    // 光線の始点
  vec3 direction; // 光線の方向ベクトル
  vec3 scatter;   // 散乱成分
  int depth;      // 反射した回数
};

struct Hit {
  float t;       // 光線の始点から衝突位置までの距離
  vec3 position; // 衝突位置
  vec3 normal;   // 衝突位置における法線ベクトル
  vec3 scatter;  // 散乱成分
  vec3 emission; // 放出成分
  int material;  // 材質
};

struct Sphere {
  vec3 center;   // 球の中心
  float radius;  // 球の半径
  vec3 scatter;  // 散乱成分
  vec3 emission; // 放出成分
  int material;  // 材質
};

uvec4 xors;

// Xorshift による疑似乱数生成
float rand() {
  uint t = (xors[0] ^ (xors[0] << 11));
  xors[0] = xors[1];
  xors[1] = xors[2];
  xors[2] = xors[3];
  xors[3] = (xors[3] ^ (xors[3] >> 19)) - (t ^ (t >> 18));
  return xors[3] / 4294967295.0f;
}

// 球と光線の交点
bool hitSphere(const in Sphere sphere, const in Ray ray, inout Hit hit) {
  vec3 oc = ray.origin - sphere.center;
  float a = dot(ray.direction, ray.direction);
  float b = dot(oc, ray.direction);
  float c = dot(oc, oc) - POW2(sphere.radius);
  float d = POW2(b) - a * c;

  float t;
  if (d > 0) {
    t = (-b - sqrt(d)) / a;
    if (0 < t && t < hit.t) {
      hit.t = t;
      hit.position = ray.origin + t * ray.direction;
      hit.normal = normalize(hit.position - sphere.center);
      hit.scatter = sphere.scatter;
      hit.emission = sphere.emission;
      hit.material = sphere.material;
      return true;
    }
    t = (-b + sqrt(d)) / a;
    if (0 < t && t < hit.t) {
      hit.t = t;
      hit.position = ray.origin + t * ray.direction;
      hit.normal = normalize(hit.position - sphere.center);
      hit.scatter = sphere.scatter;
      hit.emission = sphere.emission;
      hit.material = sphere.material;
      return true;
    }
  }

  return false;
}

// 鏡面
void mirror(inout Ray ray, const in Hit hit) {
  if (dot(-ray.direction, hit.normal) < 0) {
    ray.depth = DEPTH_MAX;
    return;
  }
  ray.depth++;
  ray.origin = hit.position + hit.normal * DELTA;
  // 課題1：鏡面の作成
  // ray.direction =
  ray.scatter *= hit.scatter;
}

float fresnel(const in float n, const in float u) {
  const float f0 = POW2((n - 1) / (n + 1));
  return f0 + (1 - f0) * POW5(1 - u);
}

// ガラス面
void glass(inout Ray ray, const in Hit hit) {
  ray.depth++;
  float n = 1.5;
  vec3 N;
  float t = dot(-ray.direction, hit.normal);
  if (t > 0.0f) {
    n = 1.0f / n;
    N = hit.normal;
    t = t;
  } else {
    n = n / 1.0f;
    N = -hit.normal;
    t = -t;
  }
  if (rand() < fresnel(n, t) || n * length(cross(N, -ray.direction)) > 1) {
    mirror(ray, hit);
  } else {
    ray.origin = hit.position - N * DELTA;
    // 課題2：ガラス面の作成
    // ray.direction =
    ray.scatter *= hit.scatter;
  }
}

// Image Based Lighting
void background(inout Ray ray, inout Hit hit) {
  ray.depth = DEPTH_MAX;
  hit.emission =
      texture(background_image,
              vec2(-atan(ray.direction.x, ray.direction.z) / (2 * PI),
                   acos(ray.direction.y) / PI))
          .rgb;
}

// 完全拡散反射面
void diffuse(inout Ray ray, const in Hit hit) {
  if (dot(-ray.direction, hit.normal) < 0) {
    ray.depth = DEPTH_MAX;
    ray.scatter = vec3(0.0f);
    return;
  }
  ray.depth++;
  ray.direction.y = sqrt(rand());
  float d = sqrt(1 - POW2(ray.direction.y));
  float v = rand() * 2.0f * PI;
  vec3 ex = vec3(1.0f, 0.0f, 0.0f);
  vec3 ey = vec3(0.0f, 1.0f, 0.0f);
  vec3 ez = vec3(0.0f, 0.0f, 1.0f);
  float dx = abs(dot(hit.normal, ex));
  float dy = abs(dot(hit.normal, ey));
  float dz = abs(dot(hit.normal, ez));
  vec3 vy = (dy < dx) ? (dz < dy) ? ez : ey : (dz < dx) ? ez : ex;
  vec3 vx = normalize(cross(vy, hit.normal));
  vec3 vz = normalize(cross(vx, hit.normal));

  ray.direction = normalize(vx * d * cos(v) + hit.normal * ray.direction.y +
                            vz * d * sin(v));
  ray.origin = hit.position + hit.normal * DELTA;
  ray.scatter *= hit.scatter;
}

// Tone Mapping
vec4 toneMap(const in vec4 color, const in float white) {
  return clamp(color * (1 + color / white) / (1 + color), 0, 1);
}

// Gamma Correction
vec4 gammaCorrect(const in vec4 color, const in float gamma) {
  float c = 1.0f / gamma;
  return vec4(pow(color.r, c), pow(color.g, c), pow(color.b, c), 0.0f);
}

void main() {
  xors = imageLoad(seed_image, group_idx.xy);

  vec4 color_present =
      (current_sample == 1) ? vec4(0.0f) : imageLoad(input_image, group_idx.xy);

  const vec3 eye = vec3(0.0f, 0.0f, 18.0f);

  const int n_sphere = 2;
  const Sphere spheres[n_sphere] = {
      {
          vec3(0.0f),
          4.0f,
          vec3(0.75f),
          vec3(0),
          DIFFUSE,
      },
      {
          vec3(0.0f, -10000.05f, 0.0f),
          9996.0f,
          vec3(0.75f),
          vec3(0),
          DIFFUSE,
      },
  };

  const mat3 M1 =
      mat3(cos(theta), 0, sin(theta), 0, 1, 0, -sin(theta), 0, cos(theta));

  const mat3 M2 = mat3(1, 0, 0, 0, cos(phi), -sin(phi), 0, sin(phi), cos(phi));

  for (int i = 0; i < SAMPLE_MAX; i++) {
    vec4 color_next = vec4(0.0f);

    const vec3 position_screen = {
        float(group_idx.x + rand()) / group_num.x * 16.0f - 8.0f,
        float(group_idx.y + rand()) / group_num.y * 9.0f - 4.5f,
        eye.z - 9.0f,
    };

    Ray ray = {
        M1 * M2 * (eye + vec3(move_x, move_y, 0)),
        M1 * M2 * (normalize(position_screen - eye)),
        vec3(1.0f),
        0,
    };

    Hit hit = {
        1000.0f, vec3(0.0f), vec3(0.0f), vec3(0.0f), vec3(0.0f), BACKGROUND,
    };

    while (ray.depth < DEPTH_MAX) {
      for (int i = 0; i < n_sphere; i++) {
        hitSphere(spheres[i], ray, hit);
      }

      switch (hit.material) {
      case BACKGROUND:
        background(ray, hit);
        break;
      case DIFFUSE:
        diffuse(ray, hit);
        break;
      case MIRROR:
        mirror(ray, hit);
        break;
      case GLASS:
        glass(ray, hit);
        break;
      }

      color_next.rgb += hit.emission * ray.scatter;

      hit.t = 10000.0f;
      hit.material = BACKGROUND;
    }

    // 平均値の逐次計算
    color_present += (color_next - color_present) / (current_sample + i);
  }

  imageStore(input_image, group_idx.xy, color_present);
  imageStore(seed_image, group_idx.xy, xors);

  output_color = gammaCorrect(toneMap(color_present, 1000.0f), 2.2);
}
