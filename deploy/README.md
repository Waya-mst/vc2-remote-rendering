## localhost でのデプロイ

Docker Image のビルド：

```sh
docker build -f deploy/Dockerfile -t demo-site:latest .
```

Docker コンテナの実行：

```sh
docker run --rm --publish 8080:80 demo-site:latest
```

コンテナ実行後，ブラウザで http://localhost:8080 にアクセスする．

## render.com でのデプロイ

- Name: `demo`
- Region: `Singapore (Southeast Asia)`
- Runtime: `Docker`
- Dockerfile Path: `deploy/Dockerfile`
