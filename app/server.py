import asyncio
import json

from websockets.server import serve

from render import Context


class WebSocket:
    def __init__(self, context):
        self.context = context

    async def task(self, websocket):
        if asyncio.current_task().cancelled():
            raise asyncio.CancelledError()

        # キャンセルされるまでサンプリングとレンダリング結果画像の送信を繰り返す
        i = 0
        while True:
            await asyncio.sleep(0.01)
            print(["-", "/", "|", "\\"][i % 4], "\r", end="")
            try:
                self.context.frame = i * self.context.sample_per_frame + 1
                self.context.render()
                i += 1
                # レンダリング結果画像を送信する（識別子：0000）
                await websocket.send(b"0000" + self.context.get_binary().getvalue())
                # 現在の1画素あたりのサンプル数を送信する（識別子：0001）
                await websocket.send(b"0001" + bytes(i * self.context.sample_per_frame))

                if self.context.maxSpp:
                    if i * self.context.sample_per_frame >= int(self.context.maxSpp):
                        break
            except RuntimeError as e:
                print("Runtime Error:", e)
                break
            except ValueError as e:
                print("ValueError:", e)
                break

    async def echo(self, websocket):
        current_task = None
        print("init")
        print("current_task: ", current_task)

        # クライアントからの接続要求を待ち受ける
        while True:
            message = json.loads(await websocket.recv())
            if "theta" in message:
                self.context.theta = message["theta"]
            if "phi" in message:
                self.context.phi = message["phi"]
            if "moveX" in message:
                self.context.moveX = message["moveX"]
            if "moveY" in message:
                self.context.moveY = message["moveY"]
            if "maxSpp" in message:
                self.context.create_shader()
                self.context.maxSpp = message["maxSpp"]

            if current_task is not None and not current_task.done():
                current_task.cancel()
                print("cancel called")
                print("current_task: ", current_task)

            # レンダリングタスクを実行する
            current_task = asyncio.create_task(self.task(websocket))

            print("task assigned")
            print("current_task: ", current_task)

    async def main(self, host, port):
        async with serve(self.echo, host, port):
            print("Listening at: ", f"ws://{host}:{port}")
            await asyncio.Future()  # run forever


if __name__ == "__main__":
    ctx = Context(width=960, height=540, sample_per_frame=64)
    ctx.bind_data(env_map_path="assets/hdr/museum_of_ethnography_1k.hdr")
    ctx.create_shader()
    ws = WebSocket(ctx)
    asyncio.run(ws.main("127.0.0.1", 8030))
