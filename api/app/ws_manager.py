from typing import Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, vehicle_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[vehicle_id] = websocket
        print(f"Vehicle {vehicle_id} connected via WebSocket")

    def disconnect(self, vehicle_id: str):
        if vehicle_id in self.active_connections:
            del self.active_connections[vehicle_id]
            print(f"Vehicle {vehicle_id} disconnected")

    async def send_command(self, vehicle_id: str, command: dict) -> bool:
        if vehicle_id in self.active_connections:
            websocket = self.active_connections[vehicle_id]
            await websocket.send_json(command)
            return True
        return False

manager = ConnectionManager()
