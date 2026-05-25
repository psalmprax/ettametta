import asyncio
import websockets

async def test_ws():
    uri = "ws://localhost:7200/ws/telemetry"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected via Nginx!")
            response = await websocket.recv()
            print(f"Received: {response}")
    except Exception as e:
        print(f"Failed via Nginx: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
