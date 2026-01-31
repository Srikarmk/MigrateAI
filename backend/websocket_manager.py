"""WebSocket connection manager for real-time updates."""

from typing import Dict, Set
from fastapi import WebSocket
import json
import asyncio


class WebSocketManager:
    """Manages WebSocket connections and broadcasts messages."""
    
    def __init__(self):
        """Initialize the WebSocket manager."""
        self.active_connections: Set[WebSocket] = set()
        self.migration_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, migration_id: str = None):
        """Connect a WebSocket client."""
        await websocket.accept()
        self.active_connections.add(websocket)
        
        if migration_id:
            if migration_id not in self.migration_connections:
                self.migration_connections[migration_id] = set()
            self.migration_connections[migration_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, migration_id: str = None):
        """Disconnect a WebSocket client."""
        self.active_connections.discard(websocket)
        if migration_id and migration_id in self.migration_connections:
            self.migration_connections[migration_id].discard(websocket)
            if not self.migration_connections[migration_id]:
                del self.migration_connections[migration_id]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending WebSocket message: {e}")
    
    async def broadcast(self, message: dict, migration_id: str = None):
        """Broadcast a message to all connected clients or specific migration."""
        if migration_id and migration_id in self.migration_connections:
            connections = self.migration_connections[migration_id]
        else:
            connections = self.active_connections
        
        disconnected = set()
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to WebSocket: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn, migration_id)
    
    async def send_agent_status(self, migration_id: str, agent: str = None, status: str = "running", component: str = None, progress: float = 0.0):
        """Send agent status update."""
        message = {
            "type": "agent_status",
            "status": status,
            "progress": progress
        }
        if agent:
            message["agent"] = agent
        if component:
            message["component"] = component
        await self.broadcast(message, migration_id)
    
    async def send_log(self, migration_id: str, level: str, message: str):
        """Send a log message."""
        await self.broadcast({
            "type": "log",
            "level": level,
            "message": message
        }, migration_id)
    
    async def send_thought_signature(self, migration_id: str, content: str):
        """Send a thought signature."""
        import time
        await self.broadcast({
            "type": "thought_signature",
            "content": content,
            "timestamp": time.time()  # Unix timestamp in seconds
        }, migration_id)
    
    async def send_components_discovered(self, migration_id: str, components: list):
        """Send discovered components."""
        await self.broadcast({
            "type": "components_discovered",
            "components": components
        }, migration_id)
    
    async def send_migration_complete(self, migration_id: str, component: str, success: bool, tests_passed: int = 0, tests_failed: int = 0):
        """Send migration completion for a component."""
        await self.broadcast({
            "type": "migration_complete",
            "component": component,
            "success": success,
            "tests_passed": tests_passed,
            "tests_failed": tests_failed
        }, migration_id)
    
    async def send_error(self, migration_id: str, message: str):
        """Send an error message."""
        await self.broadcast({
            "type": "error",
            "message": message
        }, migration_id)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
