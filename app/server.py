import asyncio
import json

from websockets.server import serve

from render import Context


class WebSocket:
    def __init__(self, context):
        self.context = context

    async def task(self, websocket):
        # キャンセルされるまでサンプリングとレンダリング結果画像の送信を繰り返す
        i = 0
        while True:
            print(["-", "/", "|", "\\"][i % 4], "\r", end="")
            try:
                self.context.current_sample = i * self.context.sample_per_frame + 1
                i += 1
                next_frame = i * self.context.sample_per_frame

                sample_max = self.context.sample_per_frame
                if self.context.max_spp:
                    if next_frame > int(self.context.max_spp):
                        sample_max = (
                            int(self.context.max_spp) % self.context.sample_per_frame
                        )
                        next_frame = int(self.context.max_spp)

                self.context.render(sample_max)

                await asyncio.gather(
                    # レンダリング結果画像を送信する（識別子：0000）
                    websocket.send(b"0000" + self.context.get_binary()),
                    # 現在の1画素あたりのサンプル数を送信する（識別子：0001）
                    websocket.send(b"0001" + bytes(next_frame)),
                )

                if self.context.max_spp:
                    if next_frame >= int(self.context.max_spp):
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
                self.context.move_x = message["moveX"]
            if "moveY" in message:
                self.context.move_y = message["moveY"]
            if "maxSpp" in message:
                self.context.max_spp = message["maxSpp"]
            if "keyValue" in message:
                self.context.key_value = message["keyValue"]

            for task in asyncio.all_tasks():
                if task.get_coro().__name__ == "task" and not task.done():
                    task.cancel()

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
    ctx.create_program()
    ws = WebSocket(ctx)
    asyncio.run(ws.main("127.0.0.1", 8030))
