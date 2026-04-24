import asyncio
import websockets
import json

async def test_telemetry():
    uri = "ws://localhost:8000/api/v1/ws/telemetry"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to telemetry")
            for _ in range(3):
                message = await websocket.recv()
                data = json.loads(message)
                print(f"Received: {data['type']}")
                if 'metrics' in data:
                    print(f"Bitrate: {data['metrics']['bitrate']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_telemetry())
