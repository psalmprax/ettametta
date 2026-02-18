from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
import json
import asyncio
import logging
import redis.asyncio as redis
from api.config import settings

router = APIRouter(prefix="/ws", tags=["websockets"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.pubsub_task = None

    async def city_connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logging.info(f"Client connected. Total connections: {len(self.active_connections)}")
        
        # Start pubsub listener if not already running
        if not self.pubsub_task:
            self.pubsub_task = asyncio.create_task(self._listen_to_redis())

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logging.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def _listen_to_redis(self):
        """
        Listens to a Redis channel and broadcasts messages to all connected clients.
        """
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe("job_updates")
        logging.info("Subscribed to Redis channel: job_updates")
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"].decode("utf-8")
                    await self.broadcast(data)
        except Exception as e:
            logging.error(f"Redis pubsub error: {e}")
        finally:
            await pubsub.unsubscribe("job_updates")
            self.pubsub_task = None

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                # Silently handle disconnected clients; they will be removed by the endpoint
                pass

manager = ConnectionManager()

@router.websocket("/jobs")
async def websocket_jobs_endpoint(websocket: WebSocket):
    await manager.city_connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@router.websocket("/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await manager.city_connect(websocket)
    try:
        import random
        while True:
            # Generate high-velocity pulse telemetry
            pulse_data = {
                "type": "telemetry_pulse",
                "timestamp": asyncio.get_event_loop().time(),
                "metrics": {
                    "bitrate": round(random.uniform(450, 980), 2),
                    "latency": round(random.uniform(12, 45), 1),
                    "signal_strength": round(random.uniform(0.85, 0.99), 3),
                    "active_nodes": random.randint(1240, 5600),
                    "global_velocity": round(random.uniform(1.2, 5.8), 2)
                },
                "active_segments": [
                    {"label": "US-EAST", "load": random.randint(20, 95)},
                    {"label": "EU-WEST", "load": random.randint(30, 85)},
                    {"label": "ASIA-PAC", "load": random.randint(10, 60)},
                    {"label": "AFRICA-NORTH", "load": random.randint(40, 90)}
                ],
                "geo_activity": [
                    {
                        "lat": round(random.uniform(-50, 70), 4),
                        "lng": round(random.uniform(-120, 140), 4),
                        "intensity": round(random.uniform(0.3, 1.0), 2)
                    } for _ in range(random.randint(1, 4))
                ]
            }
            await websocket.send_text(json.dumps(pulse_data))
            await asyncio.sleep(0.5) # High frequency pulse
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logging.error(f"Telemetry WebSocket error: {e}")
        manager.disconnect(websocket)

def notify_job_update_sync(job_data: Dict):
    """
    Synchronous utility (for Celery) to publish job updates to Redis.
    """
    import redis as redis_sync
    r = redis_sync.from_url(settings.REDIS_URL)
    message = json.dumps({
        "type": "job_update",
        "data": job_data
    })
    r.publish("job_updates", message)
