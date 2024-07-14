import cv2

from app.render import Context

ctx = Context()
ctx.bind_data(env_map_path="tests/data/test_env_map.hdr")
ctx.create_program()
ctx.render(1)
cv2.imwrite("tests/data/reference.jpg", ctx.get_buffer())
