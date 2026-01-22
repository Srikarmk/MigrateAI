"""FastAPI entry point for MigrateAI."""

import os
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from backend.models import MigrationRequest, MigrationResponse, MigrationStatus
from backend.state import state_manager
from backend.agents.ingest import IngestAgent
from backend.agents.analyze import AnalyzeAgent

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    await state_manager.initialize()
    yield
    # Shutdown
    await state_manager.close()


app = FastAPI(
    title="MigrateAI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "MigrateAI API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/migrate/start", response_model=MigrationResponse)
async def start_migration(request: MigrationRequest):
    """
    Start a new migration.
    
    Args:
        request: Migration request with repo URL and branch
    
    Returns:
        Migration response with migration ID
    """
    try:
        # Generate migration ID
        migration_id = str(uuid.uuid4())
        
        # Create migration record
        await state_manager.create_migration(
            migration_id=migration_id,
            repo_url=request.repo_url,
            branch=request.branch or "main"
        )
        
        # Update status to ingesting
        await state_manager.update_migration(
            migration_id,
            status=MigrationStatus.INGESTING.value
        )
        
        # Start ingestion (async, non-blocking)
        # In production, this would be handled by a background task or queue
        ingest_agent = IngestAgent()
        ingest_result = await ingest_agent.ingest(request.repo_url, request.branch or "main")
        
        # Update state with ingestion results
        await state_manager.update_migration(
            migration_id,
            status=MigrationStatus.ANALYZING.value,
            file_tree=ingest_result["file_tree"]
        )
        
        # Start analysis
        analyze_agent = AnalyzeAgent()
        analysis_result = await analyze_agent.analyze(
            ingest_result["react_files"],
            ingest_result["repo_path"]
        )
        
        # Update state with analysis results
        await state_manager.update_migration(
            migration_id,
            status=MigrationStatus.PLANNING.value,
            detected_components=analysis_result["class_components"]
        )
        
        return MigrationResponse(
            migration_id=migration_id,
            status=MigrationStatus.PLANNING,
            message=f"Migration started. Found {analysis_result['total_components']} class components."
        )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "migration_id": migration_id if 'migration_id' in locals() else None
            }
        )


@app.get("/api/migrate/{migration_id}")
async def get_migration_status(migration_id: str):
    """
    Get the status of a migration.
    
    Args:
        migration_id: ID of the migration
    
    Returns:
        Migration state
    """
    migration = await state_manager.get_migration(migration_id)
    if not migration:
        return JSONResponse(
            status_code=404,
            content={"error": "Migration not found"}
        )
    return migration


@app.websocket("/ws/{migration_id}")
async def websocket_endpoint(websocket: WebSocket, migration_id: str):
    """
    WebSocket endpoint for real-time migration updates.
    
    Args:
        websocket: WebSocket connection
        migration_id: ID of the migration
    """
    await websocket.accept()
    
    try:
        while True:
            # Send migration status updates
            migration = await state_manager.get_migration(migration_id)
            if migration:
                await websocket.send_json(migration)
            
            # Wait for client message or timeout
            try:
                data = await websocket.receive_text()
                # Handle client messages if needed
            except:
                pass
            
            # In production, use asyncio.sleep or proper event-driven updates
            import asyncio
            await asyncio.sleep(1)
    
    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
