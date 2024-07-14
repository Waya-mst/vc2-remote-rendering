# このファイルは moderngl が 5.8.2 から 5.9.0 に更新された際に削除された moderngl/__main__.py を復元したもの
# これまで python -m moderngl を実行することで，動作環境を確認できていたが，これからは python -m app で確認する
# cf.) https://github.com/moderngl/moderngl/commit/ca72c6e8a2fa7416f3e69d857b640dd63c64d83a

import argparse
import json
import os
import subprocess
import sys
from typing import List, Optional

import moderngl


def main(argv: Optional[List[str]] = None) -> None:
    """Entrypoint when running moderngl module."""
    version = 'moderngl %s' % moderngl.__version__

    if os.path.isfile(os.path.join(os.path.dirname(__file__), 'README.md')):
        try:
            head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], stderr=subprocess.DEVNULL)
            version += ' (%s)' % head.decode()[:8]
        except Exception:
            version += ' (archive)'

    parser = argparse.ArgumentParser(prog='moderngl')
    parser.add_argument('-v', '--version', action='version', version=version)
    parser.add_argument('--info', action='store_true', default=False)
    args = parser.parse_args(argv)

    try:
        ctx = moderngl.create_standalone_context()
    except Exception:
        if sys.platform == 'linux':
            ctx = moderngl.create_standalone_context(backend='egl')
        else:
            raise

    if args.info:
        print(json.dumps(ctx.info, sort_keys=True, indent=4))

    else:
        print(version)
        print('-' * len(version))
        print('vendor:', ctx.info['GL_VENDOR'])
        print('renderer:', ctx.info['GL_RENDERER'])
        print('version:', ctx.info['GL_VERSION'])
        print('python:', sys.version)
        print('platform:', sys.platform)
        print('code:', ctx.version_code)


if __name__ == '__main__':
    main()
