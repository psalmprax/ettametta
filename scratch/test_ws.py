import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://149.104.110.122:7200/ws/telemetry"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Received message type: {data.get('type')}")
            print(f"Details: {data}")
    except Exception as e:
        print(f"Failed to connect/read: {e}")

asyncio.run(test_websocket())
