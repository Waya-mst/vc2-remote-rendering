#version 430

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

layout(local_size_x = 1, local_size_y = 1) in;

uniform int frame;
uniform float theta;
uniform float phi;
uniform float moveX;
uniform float moveY;

layout(binding = 1, rgba32f) uniform image2D input_image;
layout(binding = 2, rgba32f) uniform image2D output_image;
layout(binding = 3, rgba32ui) uniform uimage2D seed_image;
layout(binding = 4) uniform sampler2D background_image;

ivec3 groupNum = ivec3(
	gl_NumWorkGroups.x * gl_WorkGroupSize.x,
	gl_NumWorkGroups.y * gl_WorkGroupSize.y,
	gl_NumWorkGroups.z * gl_WorkGroupSize.z
);
ivec3 groupIdx = ivec3(
	gl_GlobalInvocationID.x,
	gl_GlobalInvocationID.y,
	gl_GlobalInvocationID.z
);

float scale = 1;

struct ray {
    vec3 origin;    // 光線の始点
    vec3 direction; // 光線の方向ベクトル
    vec3 scatter;   // 散乱成分
    uint depth;     // 反射した回数
};

struct hit {
    float t;        // 光線の始点から衝突位置までの距離
    vec3 position;  // 衝突位置
    vec3 normal;    // 衝突位置における法線ベクトル
    vec3 scatter;   // 散乱成分
    vec3 emission;  // 放出成分
    uint material;  // 材質
};

struct sphere {
    vec3 center;    // 球の中心
    float radius;   // 球の半径
    vec3 scatter;   // 散乱成分
    vec3 emission;  // 放出成分
    uint material;  // 材質
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
bool hit_sphere(const in sphere s, const in ray r, inout hit h) {
    vec3 oc = r.origin - s.center;
    float a = dot(r.direction, r.direction);
    float b = dot(oc, r.direction);
    float c = dot(oc, oc) - POW2(s.radius);
    float d = POW2(b) - a * c;

    float t;
    if (d > 0)
    {
        t = (-b - sqrt(d)) / a;
        if (0 < t && t < h.t)
        {
            h.t = t;
            h.position = r.origin + t * r.direction;
            h.normal = normalize(h.position - s.center);
            h.scatter = s.scatter;
            h.emission = s.emission;
            h.material = s.material;
            return true;
        }
        t = (-b + sqrt(d)) / a;
        if (0 < t && t < h.t)
        {
            h.t = t;
            h.position = r.origin + t * r.direction;
            h.normal = normalize(h.position - s.center);
            h.scatter = s.scatter;
            h.emission = s.emission;
            h.material = s.material;
            return true;
        }
    }

    return false;
}

// 鏡面
void mirror(inout ray r, const in hit h)
{
	if (dot(-r.direction, h.normal) < 0)
	{
        r.depth = DEPTH_MAX;
		return;
	}
    r.depth++;
	r.origin = h.position + h.normal * DELTA;
    // 課題1：鏡面の作成
	// r.direction =
	r.scatter *= h.scatter;
}

float fresnel(const in float n, const in float u)
{
	const float f0 = POW2((n - 1) / (n + 1));
	return f0 + (1 - f0) * POW5(1 - u);
}

// ガラス面
void glass(inout ray r, const in hit h)
{
    r.depth++;
	float n = 1.5;
	vec3 N;
	float t = dot(-r.direction, h.normal);
	if (t > 0.0f)
	{
		n = 1.0f / n;
		N = h.normal;
		t = t;
	}
	else
	{
		n = n / 1.0f;
		N = -h.normal;
		t = -t;
	}
	if (rand() < fresnel(n, t) || n * length(cross(N, -r.direction)) > 1)
	{
		mirror(r, h);
	}
	else
	{
		r.origin = h.position - N * DELTA;
        // 課題2：ガラス面の作成
		// r.direction =
		r.scatter *= h.scatter;
	}
}

// Image Based Lighting
void background(inout ray r, inout hit h) {
    r.depth = DEPTH_MAX;
    h.emission = texture(
        background_image,
        vec2(
            -atan(r.direction.x, r.direction.z) / (2 * PI),
             acos(r.direction.y) / PI
        )
    ).rgb;
}

// 完全拡散反射面
void diffuse(inout ray r, const in hit h) {
    if (dot(-r.direction, h.normal) < 0) {
        r.depth = DEPTH_MAX;
        r.scatter = vec3(0.0f);
        return;
    }
    r.depth++;
    r.direction.y = sqrt(rand());
    float d = sqrt(1 - POW2(r.direction.y));
    float v = rand() * 2.0f * PI;
    vec3 ex = vec3(1.0f, 0.0f, 0.0f);
    vec3 ey = vec3(0.0f, 1.0f, 0.0f);
    vec3 ez = vec3(0.0f, 0.0f, 1.0f);
    float dx = abs(dot(h.normal, ex));
    float dy = abs(dot(h.normal, ey));
    float dz = abs(dot(h.normal, ez));
    vec3 vy = (dy < dx) ? (dz < dy) ? ez : ey : (dz < dx) ? ez : ex;
    vec3 vx = normalize(cross(vy, h.normal));
    vec3 vz = normalize(cross(vx, h.normal));

    r.direction = normalize(vx * d * cos(v) + h.normal * r.direction.y + vz * d * sin(v));
    r.origin = h.position + h.normal * DELTA;
    r.scatter *= h.scatter;
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
    xors = imageLoad(seed_image, groupIdx.xy);

    vec4 color_present = (frame == 1) ? vec4(0.0f) : imageLoad(input_image, groupIdx.xy);

    const vec3 eye = vec3(0.0f, 0.0f, 18.0f);

    const uint n_sphere = 2;
    const sphere ss[n_sphere] = {
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

    const mat3 M1 = mat3(
        cos(theta), 0, sin(theta),
        0, 1, 0,
        -sin(theta), 0, cos(theta)
    );

	const mat3 M2 = mat3(
		1, 0, 0,
		0, cos(phi), -sin(phi),
		0, sin(phi), cos(phi)
	);

    for (int i = 0; i < SAMPLE_MAX; i++) {
        vec4 color_next = vec4(0.0f);

        const vec3 position_screen = {
            float(groupIdx.x + rand()) / groupNum.x * 16.0f - 8.0f,
            float(groupIdx.y + rand()) / groupNum.y *  9.0f - 4.5f,
            eye.z - 9.0f,
        };

        ray r = {
            M1 * M2 * (eye + vec3(moveX, moveY, scale - 1)),
            M1 * M2 * (normalize(position_screen - eye)),
            vec3(1.0f),
            0,
        };

        hit h = {
            1000.0f,
            vec3(0.0f),
            vec3(0.0f),
            vec3(0.0f),
            vec3(0.0f),
            BACKGROUND,
        };

        while (r.depth < DEPTH_MAX) {
            for (int i = 0; i < n_sphere; i++) {
                hit_sphere(ss[i], r, h);
            }

            switch (h.material) {
                case BACKGROUND: background(r, h); break;
                case DIFFUSE: diffuse(r, h); break;
                case MIRROR: mirror(r, h); break;
                case GLASS: glass(r, h); break;
            }

            color_next.rgb += h.emission * r.scatter;

            h.t = 10000.0f;
            h.material = BACKGROUND;
        }

        // 平均値の逐次計算
        color_present += (color_next - color_present) / (frame + i);
    }

    imageStore(input_image, groupIdx.xy, color_present);
    imageStore(output_image, groupIdx.xy, gammaCorrect(toneMap(color_present, 1000.0f), 2.2));
    imageStore(seed_image, groupIdx.xy, xors);
}
