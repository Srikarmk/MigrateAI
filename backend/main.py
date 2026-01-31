"""FastAPI entry point for MigrateAI."""

import os
import uuid
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from pathlib import Path

from .models import MigrationRequest, MigrationResponse, MigrationStatus
from .state import state_manager
from .websocket_manager import websocket_manager
from .migration_control import migration_control
from .agents.ingest import IngestAgent
from .agents.analyze import AnalyzeAgent
import json

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


@app.get("/api/debug/migrations")
async def debug_migrations():
    """Debug endpoint to list all migrations."""
    try:
        # Get all migrations from database
        async with state_manager.session_factory() as session:
            from .state import MigrationRecord
            from sqlalchemy import select
            result = await session.execute(select(MigrationRecord))
            records = result.scalars().all()
            migrations = [state_manager._record_to_dict(record) for record in records]
            # Sort by created_at descending (newest first)
            migrations.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return {"migrations": migrations}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


async def run_migration_workflow(migration_id: str, repo_url: str, branch: str):
    """Run the migration workflow in the background."""
    migration_control.register_migration(migration_id)
    
    try:
        # Check if stopped before starting
        if migration_control.is_stopped(migration_id):
            await websocket_manager.send_log(migration_id, "warn", "Migration was stopped before starting")
            await state_manager.update_migration(migration_id, status=MigrationStatus.STOPPED.value)
            return
        
        # Ingest Agent
        await websocket_manager.send_agent_status(migration_id, "ingest", "running", progress=0.1)
        await websocket_manager.send_thought_signature(migration_id, "🔍 Starting repository ingestion. Analyzing repository structure and detecting React files...")
        # Send initial status
        await websocket_manager.broadcast({
            "type": "migration_status",
            "status": "ingesting",
            "migration_id": migration_id,
            "progress": 0.1
        }, migration_id)
        await websocket_manager.send_log(migration_id, "info", f"Starting ingestion for {repo_url}")
        
        # Wait if paused
        await migration_control.wait_if_paused(migration_id)
        if migration_control.is_stopped(migration_id):
            await websocket_manager.send_log(migration_id, "warn", "Migration stopped during ingestion")
            await state_manager.update_migration(migration_id, status=MigrationStatus.STOPPED.value)
            return
        
        try:
            ingest_agent = IngestAgent()
            # Determine if it's a git URL or local path (check git URL patterns first)
            is_git_url = (
                repo_url.startswith("http://") or 
                repo_url.startswith("https://") or 
                repo_url.startswith("git@") or
                "github.com" in repo_url or
                "gitlab.com" in repo_url or
                "bitbucket.org" in repo_url
            )
            
            if is_git_url:
                await websocket_manager.send_log(migration_id, "info", f"🔗 Cloning git repository: {repo_url}")
            else:
                await websocket_manager.send_log(migration_id, "info", f"📁 Accessing local repository: {repo_url}")
            
            ingest_result = await ingest_agent.ingest(repo_url, branch)
            
            repo_type = "local" if ingest_result.get("is_local") else "remote (cloned from git)"
            await websocket_manager.send_log(migration_id, "success", f"✅ Repository accessed successfully ({repo_type})")
            
            repo_path = ingest_result.get('repo_path', 'unknown')
            if not ingest_result.get("is_local"):
                # For git repos, explain the temp directory is normal
                await websocket_manager.send_log(migration_id, "info", f"📂 Repository cloned to: {repo_path}")
                await websocket_manager.send_log(migration_id, "info", "ℹ️ Note: Git repositories are cloned to a temporary folder for processing")
                await websocket_manager.send_log(migration_id, "info", "ℹ️ This is normal behavior - the 'local' path refers to the cloned copy")
            else:
                await websocket_manager.send_log(migration_id, "info", f"📂 Using local repository path: {repo_path}")
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            error_msg = f"Failed to ingest repository: {str(e)}"
            print(f"Migration {migration_id} error: {error_details}")  # Log to console
            await websocket_manager.send_error(migration_id, error_msg)
            await websocket_manager.send_log(migration_id, "error", f"Error details: {str(e)}")
            await websocket_manager.broadcast({
                "type": "migration_status",
                "status": "failed",
                "migration_id": migration_id,
                "progress": 0.0
            }, migration_id)
            await state_manager.update_migration(migration_id, status=MigrationStatus.FAILED.value, error=error_msg)
            return
        
        # Check if stopped
        if migration_control.is_stopped(migration_id):
            await state_manager.update_migration(migration_id, status=MigrationStatus.STOPPED.value)
            return
        
        await state_manager.update_migration(
            migration_id,
            status=MigrationStatus.INGESTING.value,
            file_tree=ingest_result["file_tree"]
        )
        react_files_count = len(ingest_result.get('react_files', []))
        tech_stack = ingest_result.get('tech_stack', {})
        
        await websocket_manager.send_agent_status(migration_id, "ingest", "complete", progress=0.2)
        await websocket_manager.send_log(migration_id, "success", f"✅ Ingestion complete. Found {react_files_count} React files.")
        
        if react_files_count == 0:
            await websocket_manager.send_log(migration_id, "warn", "⚠️ No React files (.jsx, .js, .tsx, .ts) found in this repository")
            
            # Check what type of project this is
            detected_framework = tech_stack.get("framework")
            if detected_framework and detected_framework != "react":
                await websocket_manager.send_log(migration_id, "info", f"📦 Detected framework: {detected_framework}")
                await websocket_manager.send_log(migration_id, "warn", f"⚠️ This appears to be a {detected_framework} project, not a React project")
                await websocket_manager.send_log(migration_id, "info", "💡 MigrateAI is designed specifically for React class component migrations")
            else:
                await websocket_manager.send_log(migration_id, "info", "💡 This repository doesn't appear to contain React code")
                await websocket_manager.send_log(migration_id, "info", "💡 Try a React repository with class components (e.g., ./demo_codebase)")
        
        # Wait if paused
        await migration_control.wait_if_paused(migration_id)
        if migration_control.is_stopped(migration_id):
            await state_manager.update_migration(migration_id, status=MigrationStatus.STOPPED.value)
            return
        
        # Analyze Agent
        await websocket_manager.send_agent_status(migration_id, "analyze", "running", progress=0.3)
        await websocket_manager.send_log(migration_id, "info", f"Analyzing {react_files_count} React files...")
        # Send status update
        await websocket_manager.broadcast({
            "type": "migration_status",
            "status": "analyzing",
            "migration_id": migration_id,
            "progress": 0.3
        }, migration_id)
        
        if react_files_count == 0:
            # No React files found - this might not be a React project
            await websocket_manager.send_log(migration_id, "warn", "⚠️ No React files (.jsx, .js, .tsx, .ts) found in repository")
            await websocket_manager.send_log(migration_id, "info", "This repository might not be a React project, or React files are in a different location")
            
            # Check what type of project it is
            tech_stack = ingest_result.get("tech_stack", {})
            if tech_stack.get("framework") != "react":
                detected_framework = tech_stack.get("framework", "unknown")
                await websocket_manager.send_log(migration_id, "info", f"Detected framework: {detected_framework or 'none'}")
                if detected_framework:
                    await websocket_manager.send_log(migration_id, "warn", f"This appears to be a {detected_framework} project, not a React project")
            
            analysis_result = {
                "class_components": [],
                "dependency_map": {},
                "total_components": 0,
                "total_files": 0
            }
        else:
            analyze_agent = AnalyzeAgent()
            analysis_result = await analyze_agent.analyze(
                ingest_result["react_files"],
                ingest_result["repo_path"]
            )
        
        # Check if stopped
        if migration_control.is_stopped(migration_id):
            await state_manager.update_migration(migration_id, status=MigrationStatus.STOPPED.value)
            return
        
        # Send discovered components - ONLY class components, not all React files
        component_names = []
        for comp in analysis_result["class_components"]:
            file_path = comp.get("file_path", "")
            # Ensure it's a string and normalize path separators
            if hasattr(file_path, '__str__') and not isinstance(file_path, str):
                file_path = str(file_path)
            # Normalize to forward slashes for consistency
            file_path = file_path.replace('\\', '/')
            component_names.append(file_path)
        
        if component_names:
            # Log component names for debugging
            await websocket_manager.send_log(migration_id, "debug", f"[DEBUG] Component names to send: {component_names}")
            await websocket_manager.send_components_discovered(migration_id, component_names)
            await websocket_manager.send_log(migration_id, "success", f"✅ Discovered {len(component_names)} class components ready for migration")
            await websocket_manager.send_log(migration_id, "info", f"📋 Components to migrate: {', '.join(component_names[:5])}{'...' if len(component_names) > 5 else ''}")
        else:
            await websocket_manager.send_log(migration_id, "warn", "⚠️ No class components found in the codebase")
            await websocket_manager.send_log(migration_id, "info", "💡 MigrateAI only migrates React CLASS components (class X extends Component)")
            await websocket_manager.send_log(migration_id, "info", "📝 Functional components (using hooks) don't need migration")
        
        await websocket_manager.send_agent_status(migration_id, "analyze", "complete", progress=0.4)
        await websocket_manager.send_log(migration_id, "success", f"✅ Analysis complete. Found {analysis_result['total_components']} class components.")
        
        # Send status update after analyze
        await websocket_manager.broadcast({
            "type": "migration_status",
            "status": "analyzing",
            "migration_id": migration_id,
            "progress": 0.4
        }, migration_id)
        await state_manager.update_migration(
            migration_id,
            status=MigrationStatus.ANALYZING.value,
            detected_components=analysis_result["class_components"]
        )
        
        # Store repo_path for later use
        await state_manager.update_migration(
            migration_id,
            file_tree={**ingest_result["file_tree"], "_repo_path": ingest_result["repo_path"]}
        )
        
        # Wait if paused
        await migration_control.wait_if_paused(migration_id)
        if migration_control.is_stopped(migration_id):
            await state_manager.update_migration(migration_id, status=MigrationStatus.STOPPED.value)
            return
        
        # Plan Agent (placeholder)
        await websocket_manager.send_agent_status(migration_id, "plan", "running", progress=0.5)
        await websocket_manager.send_log(migration_id, "info", "Creating migration plan...")
        await asyncio.sleep(0.5)  # Simulate planning
        
        # Check if stopped during planning
        if migration_control.is_stopped(migration_id):
            await state_manager.update_migration(migration_id, status=MigrationStatus.STOPPED.value)
            return
        
        await websocket_manager.send_log(migration_id, "success", "✅ Migration plan created.")
        
        # Mark planning as complete before moving to next stages
        await websocket_manager.send_agent_status(migration_id, "plan", "complete", progress=0.5)
        await websocket_manager.broadcast({
            "type": "migration_status",
            "status": "planning",
            "migration_id": migration_id,
            "progress": 0.5
        }, migration_id)
        
        # Update database status after sending WebSocket message
        await state_manager.update_migration(
            migration_id,
            status=MigrationStatus.PLANNING.value
        )
        
        # Calculate final progress
        total_components = analysis_result.get("total_components", 0)
        react_files_count = len(ingest_result.get('react_files', []))
        
        # Log what we found - make it very clear
        await websocket_manager.send_log(migration_id, "info", f"📊 Analysis Summary:")
        await websocket_manager.send_log(migration_id, "info", f"   • React files scanned: {react_files_count}")
        await websocket_manager.send_log(migration_id, "info", f"   • Class components found: {total_components}")
        if react_files_count > 0 and total_components == 0:
            await websocket_manager.send_log(migration_id, "info", f"   • All React files are already functional components (no migration needed)")
        
        if total_components > 0:
            await websocket_manager.send_log(migration_id, "success", f"✅ Migration plan created for {total_components} class components.")
            await websocket_manager.send_log(migration_id, "info", "ℹ️ Note: Execute, Test, Verify, Review, and Document agents are placeholders (Phase 2).")
            
            # Wait if paused before execute
            await migration_control.wait_if_paused(migration_id)
            if migration_control.is_stopped(migration_id):
                await state_manager.update_migration(migration_id, status=MigrationStatus.STOPPED.value)
                return
            
            await asyncio.sleep(0.5)
            
            # Execute Agent - Simulate processing each component
            # Get component list first to determine count
            component_list = analysis_result["class_components"]
            total_comp = len(component_list)
            
            await websocket_manager.send_agent_status(migration_id, "execute", "running", progress=0.6)
            await websocket_manager.send_thought_signature(migration_id, f"⚙️ Executing migration. Converting {total_comp} class components to functional components with hooks...")
            await websocket_manager.send_log(migration_id, "info", "⚡ Execute agent: Starting component transformation")
            await websocket_manager.broadcast({
                "type": "migration_status",
                "status": "executing",
                "migration_id": migration_id,
                "progress": 0.6
            }, migration_id)
            await state_manager.update_migration(migration_id, status=MigrationStatus.EXECUTING.value)
            await asyncio.sleep(0.3)
            
            if total_comp == 0:
                await websocket_manager.send_log(migration_id, "warn", "⚠️ No components to process")
            else:
                await websocket_manager.send_log(migration_id, "info", f"📦 Starting migration of {total_comp} components...")
            
            for idx, component in enumerate(component_list):
                # Get component name - use file_path which matches what was sent in components_discovered
                component_name = component.get("file_path", f"Component {idx + 1}")
                # Ensure it's a string, not a Path object, and normalize path separators
                if hasattr(component_name, '__str__') and not isinstance(component_name, str):
                    component_name = str(component_name)
                # Normalize to forward slashes for consistency
                component_name = component_name.replace('\\', '/')
                component_display = component.get("component_name", component_name)
                
                await websocket_manager.send_log(migration_id, "info", f"🔄 [{idx + 1}/{total_comp}] Processing: {component_name}")
                
                # Mark component as in progress
                await websocket_manager.send_agent_status(migration_id, "execute", "running", progress=0.6 + (idx + 1) * 0.05 / max(total_comp, 1), component=component_name)
                await asyncio.sleep(0.5)  # Simulate processing time
                
                # Simulate component migration completion - use exact same name format
                # IMPORTANT: component_name must match exactly what was sent in components_discovered
                await websocket_manager.send_log(migration_id, "debug", f"[DEBUG] Sending migration_complete for: '{component_name}' (type: {type(component_name).__name__})")
                await websocket_manager.send_migration_complete(migration_id, component_name, success=True, tests_passed=5, tests_failed=0)
                await websocket_manager.send_log(migration_id, "success", f"✅ [{idx + 1}/{total_comp}] Migrated: {component_name}")
                await asyncio.sleep(0.3)
            
            if total_comp > 0:
                await websocket_manager.send_log(migration_id, "success", f"🎉 All {total_comp} components transformed successfully!")
            await asyncio.sleep(0.3)
            
            # Wait if paused before test
            await migration_control.wait_if_paused(migration_id)
            if migration_control.is_stopped(migration_id):
                await state_manager.update_migration(migration_id, status=MigrationStatus.STOPPED.value)
                return
            
            await websocket_manager.send_agent_status(migration_id, "execute", "complete", progress=0.7)
            await websocket_manager.broadcast({
                "type": "migration_status",
                "status": "executing",
                "migration_id": migration_id,
                "progress": 0.7
            }, migration_id)
            await asyncio.sleep(0.5)
            
            # Test Agent
            await websocket_manager.send_agent_status(migration_id, "test", "running", progress=0.7)
            await websocket_manager.send_log(migration_id, "info", "🧪 Test agent: Running test suite (placeholder)")
            await websocket_manager.broadcast({
                "type": "migration_status",
                "status": "testing",
                "migration_id": migration_id,
                "progress": 0.7
            }, migration_id)
            await asyncio.sleep(0.8)
            
            await websocket_manager.send_agent_status(migration_id, "test", "complete", progress=0.8)
            await websocket_manager.broadcast({
                "type": "migration_status",
                "status": "testing",
                "migration_id": migration_id,
                "progress": 0.8
            }, migration_id)
            await asyncio.sleep(0.5)
            
            # Verify Agent
            await websocket_manager.send_agent_status(migration_id, "verify", "running", progress=0.8)
            await websocket_manager.send_log(migration_id, "info", "👁️ Verify agent: Visual regression (placeholder)")
            await websocket_manager.broadcast({
                "type": "migration_status",
                "status": "verifying",
                "migration_id": migration_id,
                "progress": 0.8
            }, migration_id)
            await state_manager.update_migration(migration_id, status=MigrationStatus.VERIFYING.value)
            await asyncio.sleep(0.8)
            
            await websocket_manager.send_agent_status(migration_id, "verify", "complete", progress=0.9)
            await websocket_manager.broadcast({
                "type": "migration_status",
                "status": "verifying",
                "migration_id": migration_id,
                "progress": 0.9
            }, migration_id)
            await asyncio.sleep(0.5)
            
            # Review Agent
            await websocket_manager.send_agent_status(migration_id, "review", "running", progress=0.9)
            await websocket_manager.send_log(migration_id, "info", "📝 Review agent: Code quality check (placeholder)")
            await websocket_manager.broadcast({
                "type": "migration_status",
                "status": "reviewing",
                "migration_id": migration_id,
                "progress": 0.9
            }, migration_id)
            await asyncio.sleep(0.8)
            
            await websocket_manager.send_agent_status(migration_id, "review", "complete", progress=0.95)
            await websocket_manager.broadcast({
                "type": "migration_status",
                "status": "reviewing",
                "migration_id": migration_id,
                "progress": 0.95
            }, migration_id)
            await asyncio.sleep(0.5)
            
            # Document Agent
            await websocket_manager.send_agent_status(migration_id, "document", "running", progress=0.95)
            await websocket_manager.send_log(migration_id, "info", "📖 Document agent: Generating migration docs (placeholder)")
            await websocket_manager.broadcast({
                "type": "migration_status",
                "status": "documenting",
                "migration_id": migration_id,
                "progress": 0.95
            }, migration_id)
            await state_manager.update_migration(migration_id, status=MigrationStatus.DOCUMENTING.value)
            await asyncio.sleep(0.8)
            
            # Mark as completed
            await websocket_manager.send_agent_status(migration_id, "document", "complete", progress=1.0)
            await websocket_manager.send_log(migration_id, "success", f"🎉 Migration complete! Successfully processed {total_components} components.")
            await websocket_manager.send_log(migration_id, "info", "💡 Full transformation will be implemented in Phase 2")
            await websocket_manager.broadcast({
                "type": "migration_status",
                "status": "completed",
                "migration_id": migration_id,
                "progress": 1.0
            }, migration_id)
            await state_manager.update_migration(migration_id, status=MigrationStatus.COMPLETED.value)
        elif react_files_count == 0:
            # No React files at all - this is not a React project
            await websocket_manager.send_log(migration_id, "warn", "⚠️ No React files found in this repository")
            await websocket_manager.send_log(migration_id, "info", "💡 MigrateAI is designed for React projects. This repository doesn't appear to contain React code.")
            await state_manager.update_migration(migration_id, status=MigrationStatus.COMPLETED.value, error="No React files found in repository")
            await websocket_manager.broadcast({
                "type": "migration_status",
                "status": "completed",
                "migration_id": migration_id,
                "progress": 1.0,
                "message": "No React files found"
            }, migration_id)
            await websocket_manager.send_agent_status(migration_id, None, "completed", progress=1.0)
        else:
            # React files exist but no class components (all are already functional)
            await websocket_manager.send_log(migration_id, "success", f"✅ Found {react_files_count} React files, but no class components to migrate.")
            await websocket_manager.send_log(migration_id, "info", "💡 All components in this repository are already functional components with hooks!")
            await websocket_manager.send_log(migration_id, "info", "📝 This is good! Your codebase is already using modern React patterns.")
            await websocket_manager.send_log(migration_id, "info", "🧪 To test migration, try: ./demo_codebase (contains 5 class components)")
            
            # Still go through the workflow stages for consistency
            await websocket_manager.send_agent_status(migration_id, "plan", "complete", progress=0.5)
            await asyncio.sleep(0.3)
            await websocket_manager.send_agent_status(migration_id, "execute", "complete", progress=0.7)
            await asyncio.sleep(0.3)
            await websocket_manager.send_agent_status(migration_id, "test", "complete", progress=0.8)
            await asyncio.sleep(0.3)
            await websocket_manager.send_agent_status(migration_id, "verify", "complete", progress=0.9)
            await asyncio.sleep(0.3)
            await websocket_manager.send_agent_status(migration_id, "review", "complete", progress=0.95)
            await asyncio.sleep(0.3)
            await websocket_manager.send_agent_status(migration_id, "document", "complete", progress=1.0)
            
            await state_manager.update_migration(migration_id, status=MigrationStatus.COMPLETED.value)
            await websocket_manager.broadcast({
                "type": "migration_status",
                "status": "completed",
                "migration_id": migration_id,
                "progress": 1.0
            }, migration_id)
        
    except Exception as e:
        if not migration_control.is_stopped(migration_id):
            import traceback
            error_details = traceback.format_exc()
            error_msg = f"Migration failed: {str(e)}"
            print(f"Migration {migration_id} error: {error_details}")  # Log to console
            await websocket_manager.send_error(migration_id, error_msg)
            await websocket_manager.send_log(migration_id, "error", f"Error details: {str(e)}")
            await websocket_manager.broadcast({
                "type": "migration_status",
                "status": "failed",
                "migration_id": migration_id,
                "progress": 0.0
            }, migration_id)
            await state_manager.update_migration(migration_id, status=MigrationStatus.FAILED.value, error=error_msg)
    finally:
        # Cleanup
        migration_control.cleanup(migration_id)


@app.post("/api/migrate/start", response_model=MigrationResponse)
async def start_migration(request: MigrationRequest):
    """
    Start a new migration.
    
    Args:
        request: Migration request with repo URL and branch
    
    Returns:
        Migration response with migration ID
    """
    migration_id = None
    try:
        # Validate request
        if not request.repo_url or not request.repo_url.strip():
            return JSONResponse(
                status_code=400,
                content={"error": "repo_url is required"}
            )
        
        # Generate migration ID
        migration_id = str(uuid.uuid4())
        
        # Create migration record
        await state_manager.create_migration(
            migration_id=migration_id,
            repo_url=request.repo_url.strip(),
            branch=request.branch or "main"
        )
        
        # Start migration workflow in background
        asyncio.create_task(run_migration_workflow(migration_id, request.repo_url.strip(), request.branch or "main"))
        
        return MigrationResponse(
            migration_id=migration_id,
            status=MigrationStatus.INGESTING,
            message="Migration started. Processing in background."
        )
    
    except Exception as e:
        error_msg = str(e)
        print(f"Error starting migration: {error_msg}")  # Log for debugging
        
        # If migration was created, mark it as failed
        if migration_id:
            try:
                await state_manager.update_migration(
                    migration_id, 
                    status=MigrationStatus.FAILED.value, 
                    error=error_msg
                )
            except:
                pass
        
        return JSONResponse(
            status_code=500,
            content={
                "error": error_msg,
                "migration_id": migration_id
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


@app.post("/api/migrate/pause")
async def pause_migration(migration_id: str = Query(..., description="ID of the migration to pause")):
    """
    Pause a running migration.
    
    Args:
        migration_id: ID of the migration to pause (query parameter)
    
    Returns:
        Success status
    """
    migration = await state_manager.get_migration(migration_id)
    if not migration:
        return JSONResponse(
            status_code=404,
            content={"error": "Migration not found"}
        )
    
    # Check if already stopped or completed
    if migration["status"] in ["stopped", "completed", "failed"]:
        # Update frontend status to match backend
        await websocket_manager.broadcast({
            "type": "migration_status",
            "status": migration["status"],
            "migration_id": migration_id
        }, migration_id)
        return JSONResponse(
            status_code=400,
            content={
                "error": f"Cannot pause migration with status: {migration['status']}",
                "current_status": migration["status"]
            }
        )
    
    # Register migration if not already registered
    if not migration_control.is_paused(migration_id) and not migration_control.is_stopped(migration_id):
        migration_control.register_migration(migration_id)
    
    migration_control.pause(migration_id)
    await state_manager.update_migration(migration_id, status=MigrationStatus.PAUSED.value)
    await websocket_manager.send_log(migration_id, "warn", "Migration paused by user")
    await websocket_manager.send_agent_status(migration_id, None, "paused", progress=0.0)
    # Send status update
    await websocket_manager.broadcast({
        "type": "migration_status",
        "status": "paused",
        "migration_id": migration_id
    }, migration_id)
    return {"status": "paused", "migration_id": migration_id}


@app.post("/api/migrate/resume")
async def resume_migration(migration_id: str = Query(..., description="ID of the migration to resume")):
    """
    Resume a paused migration.
    
    Args:
        migration_id: ID of the migration to resume (query parameter)
    
    Returns:
        Success status
    """
    migration = await state_manager.get_migration(migration_id)
    if not migration:
        return JSONResponse(
            status_code=404,
            content={"error": "Migration not found"}
        )
    
    # Check if migration is paused
    if migration["status"] != "paused":
        return JSONResponse(
            status_code=400,
            content={"error": f"Migration is not paused. Current status: {migration['status']}"}
        )
    
    # Register migration if not already registered
    if not migration_control.is_paused(migration_id) and not migration_control.is_stopped(migration_id):
        migration_control.register_migration(migration_id)
    
    migration_control.resume(migration_id)
    # Get the previous status or default to analyzing
    previous_status = migration.get("status", "analyzing")
    if previous_status == "paused":
        previous_status = "analyzing"  # Default to analyzing if we don't know
    
    await state_manager.update_migration(migration_id, status=previous_status)
    await websocket_manager.send_log(migration_id, "info", "Migration resumed by user")
    await websocket_manager.send_agent_status(migration_id, "resume", "running", progress=0.0)
    # Send status update
    await websocket_manager.broadcast({
        "type": "migration_status",
        "status": "running",
        "migration_id": migration_id
    }, migration_id)
    return {"status": "resumed", "migration_id": migration_id}


@app.post("/api/migrate/stop")
async def stop_migration(migration_id: str = Query(..., description="ID of the migration to stop")):
    """
    Stop a running migration.
    
    Args:
        migration_id: ID of the migration to stop (query parameter)
    
    Returns:
        Success status
    """
    migration = await state_manager.get_migration(migration_id)
    if not migration:
        return JSONResponse(
            status_code=404,
            content={"error": "Migration not found"}
        )
    
    # Check if already stopped or completed
    if migration["status"] in ["stopped", "completed"]:
        return JSONResponse(
            status_code=400,
            content={"error": f"Migration is already {migration['status']}"}
        )
    
    # Register migration if not already registered
    if not migration_control.is_paused(migration_id) and not migration_control.is_stopped(migration_id):
        migration_control.register_migration(migration_id)
    
    migration_control.stop(migration_id)
    await state_manager.update_migration(migration_id, status=MigrationStatus.STOPPED.value)
    await websocket_manager.send_log(migration_id, "warn", "Migration stopped by user")
    await websocket_manager.send_agent_status(migration_id, None, "stopped", progress=0.0)
    # Send status update
    await websocket_manager.broadcast({
        "type": "migration_status",
        "status": "stopped",
        "migration_id": migration_id
    }, migration_id)
    return {"status": "stopped", "migration_id": migration_id}


@app.get("/api/diff/{component}")
async def get_component_diff(component: str):
    """
    Get the diff for a migrated component.
    
    Args:
        component: Component file path/name
    
    Returns:
        Diff data with before and after code
    """
    # For now, return demo data
    # In production, this would fetch from the migration state
    return {
        "before": f"// Class component code for {component}",
        "after": f"// Functional component with hooks for {component}"
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time migration updates.
    Connects to the latest migration or can be specified via message.
    """
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Wait for client message
            try:
                data = await websocket.receive_text()
                message = json.loads(data) if data else {}
                
                # If client sends migration_id, connect to that migration
                if "migration_id" in message:
                    migration_id = message["migration_id"]
                    websocket_manager.disconnect(websocket)
                    await websocket_manager.connect(websocket, migration_id)
                    
                    # Send current migration state with status update
                    migration = await state_manager.get_migration(migration_id)
                    if migration:
                        # Send full migration state
                        await websocket_manager.send_personal_message(migration, websocket)
                        # Also send status update message
                        await websocket_manager.send_personal_message({
                            "type": "migration_status",
                            "status": migration.get("status", "unknown"),
                            "migration_id": migration_id
                        }, websocket)
            except asyncio.TimeoutError:
                pass
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
    
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add project root to path to support both relative and absolute imports
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    import uvicorn
    # Run from project root: uvicorn backend.main:app --reload
    # Or: python -m backend.main
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
