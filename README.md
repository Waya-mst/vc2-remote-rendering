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
pip intall -r requirements.txt
```

なお，`requirements.txt` は以下のコマンドで生成されている：
```bash
pip freeze > requirements.txt
```

開発環境の場合は，`requirements_dev.txt` を用いてインストールする（black, pyflakes, nbformat の依存パッケージが含まれる）：
```bash
pip intall -r requirements_dev.txt
```

## 環境マップのダウンロード

```bash
wget -nc https://dl.polyhaven.org/file/ph-assets/HDRIs/exr/1k/museum_of_ethnography_1k.exr
```

## サーバの起動

仮想環境を有効化し，依存パッケージもインストールした状態で以下のコマンドを実行：
```bash
python server.py
```

すると，ウェブソケットサーバが起動し，リッスン状態になる．

## ブラウザからのアクセス

`index.html` をブラウザで開き，start ボタンを押下すると，レンダリングが開始される．

画像領域にイベントリスナーが存在し，以下の挙動に対応している：
- 左ボタンでドラッグするとカメラ回転
- 右ボタンでドラッグするとカメラ移動


## （開発者向け）Google Colaboratory 用の notebook を生成する

仮想環境を有効化し，依存パッケージもインストールした状態で以下のコマンドを実行：
```bash
python colab/notebook.py
```

すると，`colab/websocket_server.ipynb` が生成される．

Google Colaboratory に生成されたファイルをアップロードすれば実行できる．

## （開発者向け）Python ファイルの Format & Lint

Format: `make black`

Lint: `make pyflakes`
