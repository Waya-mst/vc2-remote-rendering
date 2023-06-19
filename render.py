import io
import os
from string import Template

import cv2
import numpy as np
import moderngl


class Context:
    def __init__(self, width=960, height=540, sample_per_frame=1):
        self.context = moderngl.create_context(standalone=True, backend="egl")

        self.width = width
        self.height = height
        self.sample_per_frame = sample_per_frame

        self.frame = 1
        self.theta = 0
        self.phi = 0
        self.moveX = 0
        self.moveY = 0

        self.output_image = None

        self.compute_shader = None

    def bind_data(self, env_map_path):
        data = np.zeros((self.height, self.width, 4)).astype("float32").tobytes()

        # サンプリングを再開するために用いる raw 画像
        input_image = self.context.texture(
            (self.width, self.height), 4, data, dtype="f4"
        )
        input_image.bind_to_image(1)

        # 送信用画像（トーンマップおよびガンマ変換適用済み）
        self.output_image = self.context.texture(
            (self.width, self.height), 4, data, dtype="f4"
        )
        self.output_image.bind_to_image(2)

        # 乱数のシード画像（各画素で別々のシード値を使用）
        seed_image = self.context.texture(
            (self.width, self.height), 4, data, dtype="f4"
        )
        seed_image.write(
            data=np.random.random_sample((self.width, self.height, 4))
            .astype("float32")
            .tobytes()
        )
        seed_image.bind_to_image(3)

        # 環境マップ画像
        os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
        env_map = cv2.imread(env_map_path, cv2.IMREAD_UNCHANGED)
        env_map = cv2.cvtColor(env_map, cv2.COLOR_BGRA2RGBA)
        env_map = env_map.reshape((env_map.shape[1], env_map.shape[0], 4))
        background_img = self.context.texture(
            (env_map.shape[0], env_map.shape[1]), 4, env_map, dtype="f4"
        )
        background_img.write(data=env_map.astype("float32").tobytes())
        self.context.sampler(texture=background_img).use(4)

    def create_shader(self):
        self.compute_shader = self.context.compute_shader(
            Template(open("compute_shader.glsl").read()).substitute(
                width=self.width, height=self.height, sample_max=self.sample_per_frame
            )
        )

    def render(self):
        if self.compute_shader is None:
            raise RuntimeError("compute_shader has not been assigned")

        self.compute_shader["frame"].value = self.frame
        self.compute_shader["theta"].value = self.theta
        self.compute_shader["phi"].value = self.phi
        self.compute_shader["moveX"].value = self.moveX
        self.compute_shader["moveY"].value = self.moveY

        self.compute_shader.run(group_x=self.width, group_y=self.height)

    def get_binary(self):
        if self.output_image is None:
            raise RuntimeError("output_image has not been assigned")

        buffer = np.frombuffer(self.output_image.read(), dtype="float32").reshape(
            self.height, self.width, 4
        )
        buffer = np.flipud(buffer)
        buffer = cv2.cvtColor(buffer, cv2.COLOR_BGRA2RGBA)
        buffer = (buffer * 255).astype(np.uint8)
        is_success, binary = cv2.imencode(".jpg", buffer)
        return io.BytesIO(binary)
