import asyncio
import os
import websockets

async def test_openai():
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
        print("CONNECTION ERROR:", type(e).__name__, str(e))


async def main():
    await test_openai()

    port = int(os.environ.get("PORT", 10000))
    server = await asyncio.start_server(
        lambda r, w: respond(w),
        "0.0.0.0",
        port
    )

    print(f"HTTP SERVER RUNNING ON PORT {port}")

    async with server:
        await server.serve_forever()


async def respond(writer):
    writer.write(
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/plain\r\n"
        b"Content-Length: 24\r\n"
        b"Connection: close\r\n\r\n"
        b"Jarvis connection test"
    )
    await writer.drain()
    writer.close()
    await writer.wait_closed()


asyncio.run(main())
