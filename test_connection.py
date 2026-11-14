import asyncio
import os
import websockets

async def main():
    try:
        async with websockets.connect(
            "wss://api.openai.com/v1/realtime?model=gpt-realtime",
            additional_headers={
                "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"
            },
            compression=None,
            ping_interval=None
        ) as ws:
            print("CONNECTED")
            print("CLOUDFLARE RAY:", ws.response.headers.get("cf-ray"))
            print("SESSION:", (await ws.recv())[:150])
            await asyncio.sleep(15)
            print("STILL CONNECTED")
    except Exception as e:
        print("ERROR:", type(e).__name__, str(e))

asyncio.run(main())
