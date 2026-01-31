"""Migration control system for pause/resume/stop functionality."""

from typing import Dict
import asyncio


class MigrationControl:
    """Manages migration control flags (pause/resume/stop)."""
    
    def __init__(self):
        """Initialize the migration control system."""
        self._controls: Dict[str, Dict[str, bool]] = {}
        self._events: Dict[str, asyncio.Event] = {}
    
    def register_migration(self, migration_id: str):
        """Register a migration for control."""
        if migration_id not in self._controls:
            self._controls[migration_id] = {"paused": False, "stopped": False}
            self._events[migration_id] = asyncio.Event()
            self._events[migration_id].set()  # Start as not paused
    
    def pause(self, migration_id: str):
        """Pause a migration."""
        if migration_id in self._controls:
            self._controls[migration_id]["paused"] = True
            if migration_id in self._events:
                self._events[migration_id].clear()
    
    def resume(self, migration_id: str):
        """Resume a paused migration."""
        if migration_id in self._controls:
            self._controls[migration_id]["paused"] = False
            if migration_id in self._events:
                self._events[migration_id].set()
    
    def stop(self, migration_id: str):
        """Stop a migration."""
        if migration_id in self._controls:
            self._controls[migration_id]["stopped"] = True
            self._controls[migration_id]["paused"] = False
            if migration_id in self._events:
                self._events[migration_id].set()  # Unblock if paused
    
    def is_paused(self, migration_id: str) -> bool:
        """Check if migration is paused."""
        return self._controls.get(migration_id, {}).get("paused", False)
    
    def is_stopped(self, migration_id: str) -> bool:
        """Check if migration is stopped."""
        return self._controls.get(migration_id, {}).get("stopped", False)
    
    async def wait_if_paused(self, migration_id: str):
        """Wait if migration is paused."""
        if migration_id in self._events:
            await self._events[migration_id].wait()
    
    def cleanup(self, migration_id: str):
        """Clean up migration control resources."""
        if migration_id in self._controls:
            del self._controls[migration_id]
        if migration_id in self._events:
            del self._events[migration_id]


# Global migration control instance
migration_control = MigrationControl()
