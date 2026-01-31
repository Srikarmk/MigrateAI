"""SQLite state management for MigrateAI."""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, String, Text, DateTime, Integer, JSON
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()


class MigrationRecord(Base):
    """SQLAlchemy model for migration records."""
    __tablename__ = "migrations"

    id = Column(String, primary_key=True)
    repo_url = Column(String, nullable=False)
    branch = Column(String, default="main")
    status = Column(String, nullable=False)
    file_tree = Column(JSON)
    detected_components = Column(JSON)
    migration_plan = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error = Column(Text)
    control_flags = Column(JSON, nullable=True, default=None)  # Control flags (optional for backward compatibility)


class StateManager:
    """Manages migration state in SQLite."""
    
    def __init__(self, db_path: str = "./migrateai.db"):
        self.db_path = db_path
        self.engine = None
        self.session_factory = None
    
    async def initialize(self):
        """Initialize the database connection."""
        # Use aiosqlite for async SQLite operations
        database_url = f"sqlite+aiosqlite:///{self.db_path}"
        self.engine = create_async_engine(database_url, echo=False)
        self.session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Add control_flags column if it doesn't exist (migration)
        await self._migrate_control_flags()
    
    async def _migrate_control_flags(self):
        """Add control_flags column if it doesn't exist."""
        try:
            from sqlalchemy import text
            async with self.engine.begin() as conn:
                # Check if column exists by trying to select it
                try:
                    await conn.execute(text("SELECT control_flags FROM migrations LIMIT 1"))
                    # Column exists, no migration needed
                    return
                except Exception:
                    # Column doesn't exist, add it
                    try:
                        await conn.execute(text("ALTER TABLE migrations ADD COLUMN control_flags TEXT"))
                        print("✓ Added control_flags column to migrations table")
                    except Exception as e:
                        # Column might already exist or table doesn't exist
                        if "duplicate column" not in str(e).lower():
                            print(f"Migration note: {e}")
        except Exception as e:
            # Table might not exist yet (will be created by create_all)
            pass
    
    async def create_migration(self, migration_id: str, repo_url: str, branch: str = "main") -> Dict[str, Any]:
        """Create a new migration record."""
        async with self.session_factory() as session:
            record = MigrationRecord(
                id=migration_id,
                repo_url=repo_url,
                branch=branch,
                status="pending",
                file_tree=None,
                detected_components=None,
                migration_plan=None,
                control_flags={"paused": False, "stopped": False}
            )
            session.add(record)
            await session.commit()
            return self._record_to_dict(record)
    
    async def get_migration(self, migration_id: str) -> Optional[Dict[str, Any]]:
        """Get a migration record by ID."""
        async with self.session_factory() as session:
            result = await session.get(MigrationRecord, migration_id)
            if result:
                return self._record_to_dict(result)
            return None
    
    async def update_migration(self, migration_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update a migration record."""
        async with self.session_factory() as session:
            record = await session.get(MigrationRecord, migration_id)
            if not record:
                return None
            
            for key, value in kwargs.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            
            record.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(record)
            return self._record_to_dict(record)
    
    def _record_to_dict(self, record: MigrationRecord) -> Dict[str, Any]:
        """Convert a MigrationRecord to a dictionary."""
        # Handle control_flags - may not exist in old databases
        control_flags = None
        if hasattr(record, 'control_flags'):
            control_flags = record.control_flags
        if control_flags is None:
            # Try to get from JSON if stored as string
            try:
                import json
                if isinstance(record.control_flags, str):
                    control_flags = json.loads(record.control_flags)
                else:
                    control_flags = {"paused": False, "stopped": False}
            except:
                control_flags = {"paused": False, "stopped": False}
        
        return {
            "migration_id": record.id,
            "repo_url": record.repo_url,
            "branch": record.branch,
            "status": record.status,
            "file_tree": record.file_tree,
            "detected_components": record.detected_components,
            "migration_plan": record.migration_plan,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
            "error": record.error,
            "control_flags": control_flags
        }
    
    async def close(self):
        """Close the database connection."""
        if self.engine:
            await self.engine.dispose()


# Global state manager instance
state_manager = StateManager()
