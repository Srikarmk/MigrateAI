"""SQLite state management for MigrateAI."""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, String, Text, DateTime, Integer, JSON
from aiosqlite import connect
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
                migration_plan=None
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
            "error": record.error
        }
    
    async def close(self):
        """Close the database connection."""
        if self.engine:
            await self.engine.dispose()


# Global state manager instance
state_manager = StateManager()
