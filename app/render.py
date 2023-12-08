import io
import os
import platform
from string import Template

import cv2
import numpy as np
import moderngl


class Context:
    ATTACHMENT_INDEX_OUTPUT_COLOR = 0
    ATTACHMENT_INDEX_INPUT_COLOR = 1
    ATTACHMENT_INDEX_SEED_VALUE = 2
    TEXTURE_UNIT_INPUT_IMAGE = 1
    TEXTURE_UNIT_SEED_IMAGE = 2
    TEXTURE_UNIT_BACKGROUND_IMAGE = 3

    def __init__(self, width=960, height=540, sample_per_frame=1):
        kwargs = {
            "standalone": True,
            "require": 330,
        }
        if platform.system() == "Linux" and "LD_PRELOAD" not in os.environ:
            kwargs["backend"] = "egl"
        self.context = moderngl.create_context(**kwargs)

        self.width = width
        self.height = height
        self.sample_per_frame = sample_per_frame

        with open("assets/glsl/vertex_shader.glsl", encoding="utf-8") as vs_f:
            self.vertex_shader_str = vs_f.read()
        with open("assets/glsl/fragment_shader.glsl", encoding="utf-8") as fs_f:
            self.fragment_shader_str = fs_f.read()

        self.current_sample = 1
        self.theta = 0
        self.phi = 0
        self.move_x = 0
        self.move_y = 0
        self.max_spp = 0

        self.switch = 0
        self.output_image = None
        self.input_image_list = None
        self.seed_image_list = None

        self.program = None
        self.vao = None
        self.fbo = None

    def bind_data(self, env_map_path):
        data = np.zeros((self.height, self.width, 4)).astype("float32").tobytes()

        # 送信用画像（トーンマップおよびガンマ変換適用済み）
        self.output_image = self.context.texture(
            (self.width, self.height), components=4, dtype="f4"
        )

        # サンプリングを再開するために用いる raw 画像
        self.input_image_list = [
            self.context.texture((self.width, self.height), 4, data, dtype="f4"),
            self.context.texture((self.width, self.height), 4, data, dtype="f4"),
        ]

        seed = (
            np.random.default_rng(0)
            .integers(
                low=0, high=2**32, size=(self.width, self.height, 4), dtype=np.uint32
            )
            .tobytes()
        )

        # 乱数のシード画像（各画素で別々のシード値を使用）
        self.seed_image_list = [
            self.context.texture((self.width, self.height), 4, seed, dtype="u4"),
            self.context.texture((self.width, self.height), 4, seed, dtype="u4"),
        ]

        # 環境マップ画像
        env_map = cv2.imread(env_map_path, cv2.IMREAD_UNCHANGED)
        env_map = cv2.cvtColor(env_map, cv2.COLOR_BGRA2RGBA)
        env_map = env_map.reshape((env_map.shape[1], env_map.shape[0], 4))
        background_image = self.context.texture(
            (env_map.shape[0], env_map.shape[1]), 4, env_map, dtype="f4"
        )
        background_image.write(data=env_map.astype("float32").tobytes())
        self.context.sampler(texture=background_image).use(
            Context.TEXTURE_UNIT_BACKGROUND_IMAGE
        )

    def create_program(self):
        self.program = self.context.program(
            vertex_shader=self.vertex_shader_str,
            fragment_shader=Template(self.fragment_shader_str).substitute(
                width=self.width,
                height=self.height,
            ),
            fragment_outputs={
                "output_color": Context.ATTACHMENT_INDEX_OUTPUT_COLOR,
                "input_color": Context.ATTACHMENT_INDEX_INPUT_COLOR,
                "seed_value": Context.ATTACHMENT_INDEX_SEED_VALUE,
            },
        )
        vbo = self.context.buffer(
            np.array(
                [
                    [-1, -1],
                    [-1, 3],
                    [3, -1],
                ],
                dtype="f4",
            )
        )
        self.vao = self.context.vertex_array(
            self.program,
            [(vbo, "2f /v", "position_vertices")],
        )

    def read_buffer(self, attachment):
        if self.fbo is None:
            raise RuntimeError("frame buffer object has not been assigned")

        return np.frombuffer(
            self.fbo.read(
                components=4,
                dtype="f4",
                attachment=attachment,
            ),
            dtype="f4",
        ).reshape(self.height, self.width, 4)

    def render(self, sample_max):
        if self.program is None:
            raise RuntimeError("program has not been created")
        if self.vao is None:
            raise RuntimeError("vertex array object has not been assigned")
        if self.output_image is None:
            raise RuntimeError("output_image has not been assigned")
        if self.input_image_list is None:
            raise RuntimeError("input_image_list has not been assigned")
        if self.seed_image_list is None:
            raise RuntimeError("seed_image_list has not been assigned")

        if self.fbo is not None:
            self.fbo.release()

        self.program["sample_max"].value = sample_max
        self.program["current_sample"].value = self.current_sample
        self.program["theta"].value = self.theta
        self.program["phi"].value = self.phi
        self.program["move_x"].value = self.move_x
        self.program["move_y"].value = self.move_y

        self.program["input_image"].value = Context.TEXTURE_UNIT_INPUT_IMAGE
        self.program["seed_image"].value = Context.TEXTURE_UNIT_SEED_IMAGE
        self.program["background_image"].value = Context.TEXTURE_UNIT_BACKGROUND_IMAGE

        self.fbo = self.context.framebuffer(
            [
                self.output_image,
                self.input_image_list[self.switch],
                self.seed_image_list[self.switch],
            ]
        )
        self.fbo.use()
        self.switch = ~self.switch & 1
        self.context.sampler(
            texture=self.input_image_list[self.switch],
            filter=(moderngl.NEAREST, moderngl.NEAREST),
        ).use(Context.ATTACHMENT_INDEX_INPUT_COLOR)
        self.context.sampler(
            texture=self.seed_image_list[self.switch],
            filter=(moderngl.NEAREST, moderngl.NEAREST),
        ).use(Context.ATTACHMENT_INDEX_SEED_VALUE)
        self.context.clear()
        self.vao.render(moderngl.TRIANGLES)

    def get_binary(self):
        buffer = self.read_buffer(Context.ATTACHMENT_INDEX_OUTPUT_COLOR)
        buffer = np.flipud(buffer)
        buffer = cv2.cvtColor(buffer, cv2.COLOR_BGRA2RGBA)
        buffer = (buffer * 255).astype(np.uint8)
        is_success, binary = cv2.imencode(".jpg", buffer)
        with io.BytesIO(binary) as b:
            return b.getvalue()
