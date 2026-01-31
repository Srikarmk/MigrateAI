# MigrateAI - Backend-Frontend Connection Summary

## Overview
The backend and frontend have been fully connected and integrated. The system now supports real-time migration tracking through WebSocket connections and REST API endpoints.

## Architecture

### Backend (FastAPI)
- **Port**: 8000
- **WebSocket**: `/ws` (connects to migrations via migration_id)
- **REST API**: `/api/*` endpoints

### Frontend (React + Vite)
- **Port**: 3000 (with proxy to backend)
- **WebSocket**: Connects to `ws://localhost:8000/ws`
- **API**: Uses proxy through Vite dev server

## API Endpoints

### 1. Start Migration
- **Endpoint**: `POST /api/migrate/start`
- **Request Body**:
  ```json
  {
    "repo_url": "https://github.com/user/repo" or "./demo_codebase",
    "branch": "main" (optional)
  }
  ```
- **Response**:
  ```json
  {
    "migration_id": "uuid",
    "status": "ingesting",
    "message": "Migration started. Processing in background."
  }
  ```

### 2. Get Migration Status
- **Endpoint**: `GET /api/migrate/{migration_id}`
- **Response**: Full migration state with file_tree, detected_components, etc.

### 3. Pause Migration
- **Endpoint**: `POST /api/migrate/pause?migration_id={migration_id}`
- **Response**: `{"status": "paused", "migration_id": "..."}`

### 4. Get Component Diff
- **Endpoint**: `GET /api/diff/{component}`
- **Response**:
  ```json
  {
    "before": "class component code",
    "after": "functional component code"
  }
  ```

## WebSocket Message Types

The backend sends structured messages that the frontend expects:

### 1. Agent Status
```json
{
  "type": "agent_status",
  "agent": "ingest|analyze|plan|execute|test|verify|review|document",
  "status": "running|complete",
  "component": "ComponentName.jsx",
  "progress": 0.0-1.0
}
```

### 2. Log Message
```json
{
  "type": "log",
  "level": "info|warn|error|success",
  "message": "Log message text"
}
```

### 3. Thought Signature
```json
{
  "type": "thought_signature",
  "content": "Agent reasoning/thinking",
  "timestamp": 1234567890.123
}
```

### 4. Components Discovered
```json
{
  "type": "components_discovered",
  "components": ["Component1.jsx", "Component2.jsx", ...]
}
```

### 5. Migration Complete
```json
{
  "type": "migration_complete",
  "component": "ComponentName.jsx",
  "success": true,
  "tests_passed": 10,
  "tests_failed": 0
}
```

### 6. Error
```json
{
  "type": "error",
  "message": "Error description"
}
```

## Frontend Components

### 1. App.jsx
- Main application component
- Manages migration state
- Handles WebSocket messages
- Connects to backend API

### 2. Dashboard.jsx
- Shows migration overview
- Displays statistics (total, completed, failed, pending)
- Shows current agent and progress

### 3. ProgressView.jsx
- Visual progress bar
- Agent timeline visualization
- Component progress tracking

### 4. FileTree.jsx
- Lists discovered components
- Shows component status (pending, running, complete, failed)
- Allows component selection

### 5. DiffViewer.jsx
- Shows before/after code comparison
- Fetches diff from `/api/diff/{component}`
- Supports split and unified view modes

### 6. LogStream.jsx
- Displays real-time logs
- Shows thought signatures
- Filterable by log level

### 7. useWebSocket.js
- Custom hook for WebSocket connection
- Auto-reconnection with exponential backoff
- Handles message parsing

## Migration Workflow

1. **User starts migration** via frontend
   - Frontend calls `POST /api/migrate/start`
   - Backend creates migration record
   - Background task starts workflow

2. **Ingest Agent** (progress: 0.0-0.2)
   - Clones/accesses repository
   - Builds file tree
   - Detects tech stack
   - Finds React files
   - Sends WebSocket updates

3. **Analyze Agent** (progress: 0.2-0.4)
   - Parses React files
   - Finds class components
   - Maps dependencies
   - Sends `components_discovered` message

4. **Plan Agent** (progress: 0.4-0.6)
   - Creates migration DAG
   - Orders components by dependencies
   - (Currently placeholder)

5. **Execute Agent** (progress: 0.6-0.7)
   - Transforms class to hooks
   - Uses Gemini 3 for transformation
   - (Currently placeholder)

6. **Test Agent** (progress: 0.7-0.8)
   - Runs tests in Docker
   - Reports results
   - (Currently placeholder)

7. **Verify Agent** (progress: 0.8-0.9)
   - Visual regression testing
   - (Currently placeholder)

8. **Review Agent** (progress: 0.9-0.95)
   - Code quality review
   - (Currently placeholder)

9. **Document Agent** (progress: 0.95-1.0)
   - Generates PR description
   - Creates migration guide
   - (Currently placeholder)

## Testing the Connection

### 1. Start Backend
```bash
# From project root (recommended)
uvicorn backend.main:app --reload

# Or use the helper script
python run_backend.py

# Or as Python module
python -m backend.main
```

### 2. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

### 3. Test Migration
- Open `http://localhost:3000`
- Enter repository URL (e.g., `./demo_codebase` for local path)
- Click "Start Migration"
- Watch real-time updates in the dashboard

### 4. Test with Demo Codebase
The `demo_codebase` folder contains 5 React class components:
- `Counter.jsx` - Simple state management
- `UserProfile.jsx` - Lifecycle methods
- `Timer.jsx` - Cleanup with componentWillUnmount
- `ContactForm.jsx` - Form handling with refs
- `DataFetcher.jsx` - API calls in lifecycle

Use local path: `./demo_codebase` or absolute path to test.

## Key Features

✅ **Real-time Updates**: WebSocket broadcasts migration progress
✅ **Component Discovery**: Automatically finds class components
✅ **Progress Tracking**: Visual progress bars and agent timeline
✅ **Log Streaming**: Real-time logs and thought signatures
✅ **Diff Viewing**: Before/after code comparison
✅ **Error Handling**: Graceful error handling and reporting
✅ **State Persistence**: SQLite database for migration state

## Next Steps (Phase 2)

- [ ] Implement Plan Agent (DAG creation)
- [ ] Implement Execute Agent (Gemini 3 transformation)
- [ ] Implement Test Agent (Docker test execution)
- [ ] Implement Verify Agent (Playwright visual regression)
- [ ] Implement Review Agent (Code quality review)
- [ ] Implement Document Agent (PR generation)
- [ ] Add LangGraph orchestrator for workflow coordination
- [ ] Store component diffs in database
- [ ] Implement actual code transformation with Gemini 3

## Environment Variables

Create `.env` file:
```
GEMINI_API_KEY=your_key_here
DATABASE_URL=sqlite:///./migrateai.db
```

## Notes

- Frontend expects WebSocket messages in specific format (see above)
- Backend supports both git URLs and local paths
- WebSocket manager handles multiple connections per migration
- State is persisted in SQLite database
- CORS is enabled for all origins (update for production)
