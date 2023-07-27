import re
import sys

import nbformat

notebook = nbformat.v4.new_notebook()

notebook.metadata.accelerator = "GPU"
notebook.metadata.kernelspec = {"name": "python3", "display_name": "Python 3"}

fragments = {}

fragments[
    "install_driver"
] = """
!apt-get install libnvidia-gl-$(grep -oP 'NVIDIA UNIX x86_64 Kernel Module\s+\K[\d.]+(?=\s+)' /proc/driver/nvidia/version | grep -oE '^[0-9]+')
"""

fragments["write_requirements.txt"] = "%%file requirements.txt\n" + re.sub(
    "==.*", "", open("requirements.txt", encoding="utf-8").read()
)

fragments[
    "install_packages"
] = """
!pip install -r requirements.txt
!pip install pyngrok ping3
"""

fragments[
    "show_moderngl_config"
] = """
!python -m moderngl
"""

fragments[
    "make_directories"
] = """
!mkdir -p app
!mkdir -p assets/glsl
!mkdir -p colab
"""

fragments["write_vertex_shader.glsl"] = (
    "%%file assets/glsl/vertex_shader.glsl\n"
    + open("assets/glsl/vertex_shader.glsl", encoding="utf-8").read()
)

fragments["write_fragment_shader.glsl"] = (
    "%%file assets/glsl/fragment_shader.glsl\n"
    + open("assets/glsl/fragment_shader.glsl", encoding="utf-8").read()
)

fragments["write_server.py"] = (
    "%%file app/server.py\n" + open("app/server.py", encoding="utf-8").read()
)

fragments["write_render.py"] = (
    "%%file app/render.py\n" + open("app/render.py", encoding="utf-8").read()
)

fragments[
    "download_environment_map"
] = """
!(mkdir -p assets/hdr && cd assets/hdr && curl -O https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/museum_of_ethnography_1k.hdr)
"""

fragments[
    "describe_instance_information"
] = """
import json
from pprint import pprint
from urllib import request

ipinfo = json.loads(request.urlopen("https://ipinfo.io").read())
pprint(ipinfo)
"""

fragments["write_tunnel.py"] = (
    "%%file colab/tunnel.py\n" + open("colab/tunnel.py", encoding="utf-8").read()
)

fragments[
    "start_tunnel"
] = """
from colab.tunnel import Tunnel

tunnel = Tunnel()

# Ngrok authtoken を指定
# authtoken の値をダッシュボード (https://dashboard.ngrok.com/get-started/your-authtoken) から取得し，フォームに入力する
# 毎回の入力を省略する場合は，authtoken の値を引数として渡す
tunnel.install_auth_token()

# Google Colaboratory のサーバと最も低遅延で通信できるトンネルを見つける
tunnel.calc_region_priority()

# グローバルアクセス可能なURLを取得する
public_url = tunnel.get_public_url(port=8030)
print(public_url.replace("tcp://", "ws://"))
"""

fragments[
    "start_up_server"
] = """
!python app/server.py
"""


def new_code_cell(identifier):
    code_cell = nbformat.v4.new_code_cell(fragments[identifier])
    # all cells have an id field which must be a string of length 1-64 with alphanumeric, -, and _ as legal characters to use.
    # cf.) https://nbformat.readthedocs.io/en/latest/format_description.html#cell-ids
    code_cell["id"] = identifier.replace(".", "_")
    return code_cell


notebook["cells"] = [
    new_code_cell("install_driver"),
    new_code_cell("write_requirements.txt"),
    new_code_cell("install_packages"),
    new_code_cell("show_moderngl_config"),
    new_code_cell("make_directories"),
    new_code_cell("write_vertex_shader.glsl"),
    new_code_cell("write_fragment_shader.glsl"),
    new_code_cell("write_server.py"),
    new_code_cell("write_render.py"),
    new_code_cell("download_environment_map"),
    new_code_cell("describe_instance_information"),
    new_code_cell("write_tunnel.py"),
    new_code_cell("start_tunnel"),
    new_code_cell("start_up_server"),
]

nbformat.write(notebook, sys.stdout)
