"""Pydantic models for MigrateAI."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class MigrationStatus(str, Enum):
    """Migration status enum."""
    PENDING = "pending"
    INGESTING = "ingesting"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    TESTING = "testing"
    VERIFYING = "verifying"
    REVIEWING = "reviewing"
    DOCUMENTING = "documenting"
    COMPLETED = "completed"
    FAILED = "failed"


class ComponentType(str, Enum):
    """Component type enum."""
    CLASS = "class"
    FUNCTIONAL = "functional"
    UNKNOWN = "unknown"


class ClassComponent(BaseModel):
    """Represents a React class component."""
    file_path: str
    component_name: str
    has_state: bool
    has_lifecycle: bool
    lifecycle_methods: List[str]
    dependencies: List[str]  # Other components/files this depends on
    state_properties: List[str]
    methods: List[str]
    uses_refs: bool
    uses_context: bool


class MigrationTask(BaseModel):
    """Represents a single migration task."""
    component: ClassComponent
    order: int
    status: MigrationStatus
    transformed_code: Optional[str] = None
    error: Optional[str] = None
    test_results: Optional[Dict[str, Any]] = None


class MigrationRequest(BaseModel):
    """Request to start a migration."""
    repo_url: str
    branch: Optional[str] = "main"
    target_directory: Optional[str] = None


class MigrationResponse(BaseModel):
    """Response from migration start."""
    migration_id: str
    status: MigrationStatus
    message: str


class MigrationState(BaseModel):
    """Current state of a migration."""
    migration_id: str
    repo_url: str
    branch: str
    status: MigrationStatus
    file_tree: Optional[Dict[str, Any]] = None
    detected_components: List[ClassComponent] = []
    migration_plan: List[MigrationTask] = []
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = None
