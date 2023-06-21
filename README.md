## レポジトリ構成

リポジトリは下記のように構成されている：

```bash
.
├── app
│   ├── render.py
│   └── server.py
├── assets
│   ├── glsl
│   │   └── compute_shader.glsl
│   ├── hdr
│   │   └── museum_of_ethnography_1k.hdr
│   ├── html
│   │   └── index.html
│   └── js
│       └── session-manager.js
├── colab
│   ├── notebook.py
│   └── websocket_server.ipynb
├── Makefile
├── README.md
├── requirements_dev.txt
└── requirements.txt

7 directories, 12 files
```

各ファイルの内容を以下に示す：

- app/render.py

  ModernGL という Python モジュールを使用して OpenGL コンテキストを生成する．生成したコンテキストを用いて，レンダリングの処理を実行する．

- app/server.py

  WebSocket サーバを起動する．クライアントからのリクエストに応じて WebSocket のコネクションを確立し，タスクが生成される．このタスクは，キャンセルのリクエストがくるまで停止しない無限ループとなっており，ループ中にレンダリングとその結果画像の送信が実行される．このループ中のレンダリングにおいて，サンプリングは継続される．WebSocket のコネクション確立後，クライアントから何らかのリクエストがあると，タスクをキャンセルして新しいタスクを生成する．新しいタスクが生成された時点で，サンプリング進捗は０に戻る．

- assets/glsl/compute_shader.glsl

  OpenGL のコンピュートシェーダーの内容が記述されている．GPU パストレーシングが実装されている．

- assets/hdr/

  イメージベーストライティングに使用する環境マップを格納する．

- assets/html/index.html

  WebSocket サーバと通信する WEB ページ．

- assets/js/session-manager.js

  WebSocket サーバに対してリクエストを送信したり，レスポンスを受信するための処理が記述されている．

- colab/notebook.py

  Google Colaboratory で実行可能なノートブックファイル (.ipynb) を生成するスクリプトが記述されている．

- colab/websocket_server.ipynb

  自動生成されたノートブックファイル．

- Makefile

  Python ファイルのフォーマットおよびリントを実行する際のターゲットが記述されている．

- README.md

  本ファイル．

- requirements.txt

  アプリケーションの実行に必要な python のパッケージが記述されている．

- requirements_dev.txt

  アプリケーションの開発に必要な python のパッケージが記述されている．

## Python3 バージョン

```bash
python3 -V
Python 3.10.6
```

## 仮想環境の構築

構築：
```bash
python3 -m venv venv
```

有効化：
```bash
. venv/bin/activate
```

無効化：
```bash
deactivate
```

## 依存パッケージのインストール

仮想環境を有効化した状態で以下のコマンドを実行：
```bash
pip install -r requirements.txt
```

なお，`requirements.txt` は以下のコマンドで生成されている：
```bash
pip freeze > requirements.txt
```

開発環境の場合は，`requirements_dev.txt` を用いてインストールする（black, pyflakes, nbformat の依存パッケージが含まれる）：
```bash
pip install -r requirements_dev.txt
```

## 環境マップのダウンロード

```bash
(mkdir -p assets/hdr && cd assets/hdr && curl -O https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/museum_of_ethnography_1k.hdr)
```

## サーバの起動

仮想環境を有効化し，依存パッケージもインストールした状態で以下のコマンドを実行：
```bash
python app/server.py
```

すると，ウェブソケットサーバが起動し，リッスン状態になる．

## ブラウザからのアクセス

`assets/html/index.html` をブラウザで開き，start ボタンを押下すると，レンダリングが開始される．

画像領域にイベントリスナーが存在し，以下の挙動に対応している：
- 左ボタンでドラッグするとカメラ回転
- 右ボタンでドラッグするとカメラ移動


## （開発者向け）Google Colaboratory 用の notebook を生成する

仮想環境を有効化し，依存パッケージもインストールした状態で以下のコマンドを実行：
```bash
make notebook
```

すると，`colab/websocket_server.ipynb` が生成される．

Google Colaboratory に生成されたファイルをアップロードすれば実行できる．

## （開発者向け）Python ファイルの Format & Lint

Format: `make black`

Lint: `make pyflakes`
