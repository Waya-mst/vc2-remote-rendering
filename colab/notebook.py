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
!pip install pyngrok
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
"""

fragments["write_compute_shader.glsl"] = (
    "%%file assets/glsl/compute_shader.glsl\n"
    + open("assets/glsl/compute_shader.glsl", encoding="utf-8").read()
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
    "get_server_region"
] = """
import json
from pprint import pprint
from urllib import request

ipinfo = json.loads(request.urlopen("https://ipinfo.io").read())
pprint(ipinfo)

# タイムゾーンの情報に基づき，サーバーに最も近いリージョンを見つける
# ngrok で指定できるリージョンは下記のとおり：
# cf.) https://ngrok.com/docs/ngrok-agent/config/#region
timezone = ipinfo["timezone"]
region_map = {
    "America": "us", # United States
    "Europe": "eu", # Europe
    "Pacific": "ap", # Asia/Pacific
    "Australia": "au", # Australia
    # "": "sa", # South America
    "Asia": "jp", # Japan
    # "": "in", # India
}
region = region_map.get(timezone.split("/")[0], "us")
"""

fragments[
    "install_ngrok_authtoken"
] = """
# Ngrok authtoken を指定
# authtoken の値をダッシュボード (https://dashboard.ngrok.com/get-started/your-authtoken) から取得し，フォームに入力する
# 毎回の入力を省略する場合は，次行の secret を authtoken の値に書き換える
auth_token = "secret"
auth_token = not auth_token == "secret" or input("auth_token: ")
"""

fragments[
    "generate_access_link"
] = """
from pyngrok import conf, ngrok

# Ngrok のトンネルのリージョンと authtoken を設定
pyngrok_config = conf.PyngrokConfig(region=region, auth_token=auth_token)

# 433 port へのアクセスを 8030 port へフォワーディング
public_url = ngrok.connect(8030, pyngrok_config=pyngrok_config).public_url
print(public_url.replace("https", "wss"))
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
    new_code_cell("write_compute_shader.glsl"),
    new_code_cell("write_server.py"),
    new_code_cell("write_render.py"),
    new_code_cell("download_environment_map"),
    new_code_cell("get_server_region"),
    new_code_cell("install_ngrok_authtoken"),
    new_code_cell("generate_access_link"),
    new_code_cell("start_up_server"),
]

nbformat.write(notebook, sys.stdout)
