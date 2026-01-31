# MigrateAI Testing Guide

Complete guide for testing both the backend API and frontend UI.

## Prerequisites

### Required Software
- **Python 3.11+** - Backend runtime
- **Node.js 18+** - Frontend runtime
- **Git** - For cloning repositories (if testing with git URLs)
- **Gemini API Key** - For AI transformations (optional for basic testing)

### Verify Installation
```bash
# Check Python version
python --version  # Should be 3.11+

# Check Node.js version
node --version  # Should be 18+

# Check Git
git --version
```

## Initial Setup

### 1. Backend Setup

```bash
# Navigate to project root
cd s:\Programming\MigrateAI

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Create .env file
cp env.example .env

# Edit .env and add your Gemini API key (optional for basic testing)
# GEMINI_API_KEY=your_key_here
# DATABASE_URL=sqlite:///./migrateai.db
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Return to project root
cd ..
```

## Starting the Services

### Option 1: Two Terminal Windows (Recommended)

**Terminal 1 - Backend:**
```bash
# From project root
python run_backend.py

# Or using uvicorn directly
uvicorn backend.main:app --reload

# Or as module
python -m backend.main
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Terminal 2 - Frontend:**
```bash
# From project root
cd frontend
npm run dev
```

**Expected Output:**
```
  VITE v5.0.8  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

### Option 2: Single Terminal (Background Processes)

**Windows PowerShell:**
```powershell
# Start backend in background
Start-Process python -ArgumentList "run_backend.py" -NoNewWindow

# Start frontend
cd frontend
npm run dev
```

**Linux/Mac:**
```bash
# Start backend in background
python run_backend.py &

# Start frontend
cd frontend
npm run dev
```

## Testing the Backend API

### 1. Health Check

```bash
# Using curl
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy"}

# Using browser
# Open: http://localhost:8000/health
```

### 2. Root Endpoint

```bash
curl http://localhost:8000/

# Expected response:
# {"message":"MigrateAI API","version":"1.0.0"}
```

### 3. Start a Migration (Local Path)

```bash
# Test with demo codebase
curl -X POST http://localhost:8000/api/migrate/start \
  -H "Content-Type: application/json" \
  -d "{\"repo_url\": \"./demo_codebase\", \"branch\": \"main\"}"

# Expected response:
# {
#   "migration_id": "uuid-here",
#   "status": "ingesting",
#   "message": "Migration started. Processing in background."
# }
```

**Save the `migration_id` from the response for next steps!**

### 4. Check Migration Status

```bash
# Replace {migration_id} with actual ID from step 3
curl http://localhost:8000/api/migrate/{migration_id}

# Expected response includes:
# {
#   "migration_id": "...",
#   "repo_url": "./demo_codebase",
#   "status": "analyzing",
#   "file_tree": {...},
#   "detected_components": [...],
#   ...
# }
```

### 5. Get Component Diff

```bash
# Test diff endpoint (returns demo data for now)
curl http://localhost:8000/api/diff/Counter.jsx

# Expected response:
# {
#   "before": "// Class component code for Counter.jsx",
#   "after": "// Functional component with hooks for Counter.jsx"
# }
```

### 6. Test WebSocket Connection

**Using Python:**
```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        # Send migration_id
        await websocket.send(json.dumps({"migration_id": "your-migration-id"}))
        
        # Listen for messages
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Received: {data}")
            if data.get("type") == "error":
                break

asyncio.run(test_websocket())
```

**Using Browser Console:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = () => {
  console.log('Connected');
  ws.send(JSON.stringify({ migration_id: 'your-migration-id' }));
};
ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};
```

## Testing the Frontend UI

### 1. Access the Frontend

Open your browser and navigate to:
```
http://localhost:3000
```

### 2. Verify Connection Status

**Check the header:**
- Look for connection status indicator (top center)
- Should show "Connected" with green dot
- If "Disconnected", check backend is running

### 3. Test Migration with Demo Codebase

**Steps:**
1. In the header, find the input field
2. Enter: `./demo_codebase` (or absolute path: `s:\Programming\MigrateAI\demo_codebase`)
3. Click "Start Migration" button
4. Watch the real-time updates

**What to Observe:**
- ✅ Connection status changes to "Connected"
- ✅ Status changes from "idle" to "running"
- ✅ Progress bar starts moving
- ✅ Agent timeline shows "ingest" → "analyze" → "plan"
- ✅ Components appear in left panel (FileTree)
- ✅ Logs appear in right panel (LogStream)
- ✅ Progress percentage increases

### 4. Test Component Selection

**Steps:**
1. Wait for components to appear in left panel
2. Click on a component (e.g., "Counter.jsx")
3. Check the center panel (DiffViewer)

**Expected:**
- Component name appears in diff viewer
- "Before" and "After" code panels show (demo data for now)
- Component is highlighted in file tree

### 5. Test Log Streaming

**Observe the LogStream panel (right side):**
- **Logs tab**: Should show info, success, warn messages
- **Thought Signatures tab**: Shows agent reasoning (when implemented)
- Messages should auto-scroll
- Filter buttons work (all, info, warn, error)

### 6. Test Progress Visualization

**Check the ProgressView (center top):**
- Progress bar fills as migration progresses
- Agent timeline shows current agent
- Completed agents show checkmark
- Current agent shows active indicator

### 7. Test Pause Functionality

**Steps:**
1. Start a migration
2. Click "Pause" button in header
3. Check logs for pause message

**Expected:**
- Status changes to "paused"
- Log shows "Migration paused by user"

## Testing Full Workflow

### Test Case 1: Local Demo Codebase

```bash
# 1. Start backend
python run_backend.py

# 2. Start frontend (new terminal)
cd frontend && npm run dev

# 3. In browser: http://localhost:3000
# 4. Enter: ./demo_codebase
# 5. Click "Start Migration"
# 6. Observe complete workflow
```

**Expected Components Found:**
- `src/components/Counter.jsx`
- `src/components/UserProfile.jsx`
- `src/components/Timer.jsx`
- `src/components/ContactForm.jsx`
- `src/components/DataFetcher.jsx`

### Test Case 2: Git Repository (if available)

```bash
# In frontend UI, enter a git URL:
https://github.com/user/repo

# Or test with a public React repo
```

### Test Case 3: Invalid Path

```bash
# Test error handling
# Enter invalid path: ./nonexistent
# Should show error in logs
```

## API Testing with Postman/Insomnia

### Collection Setup

**Base URL:** `http://localhost:8000`

### Endpoints to Test

1. **GET /health**
   - Method: GET
   - URL: `http://localhost:8000/health`
   - Expected: 200 OK, `{"status":"healthy"}`

2. **POST /api/migrate/start**
   - Method: POST
   - URL: `http://localhost:8000/api/migrate/start`
   - Headers: `Content-Type: application/json`
   - Body (JSON):
     ```json
     {
       "repo_url": "./demo_codebase",
       "branch": "main"
     }
     ```
   - Expected: 200 OK, migration_id returned

3. **GET /api/migrate/{migration_id}**
   - Method: GET
   - URL: `http://localhost:8000/api/migrate/{migration_id}`
   - Expected: 200 OK, migration state

4. **GET /api/diff/{component}**
   - Method: GET
   - URL: `http://localhost:8000/api/diff/Counter.jsx`
   - Expected: 200 OK, diff data

5. **POST /api/migrate/pause**
   - Method: POST
   - URL: `http://localhost:8000/api/migrate/pause?migration_id={migration_id}`
   - Expected: 200 OK, pause confirmation

## WebSocket Testing

### Using wscat (if installed)

```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8000/ws

# Send migration_id
{"migration_id": "your-migration-id"}

# Observe incoming messages
```

### Using Browser DevTools

1. Open browser console (F12)
2. Run:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = () => {
  console.log('✅ Connected');
  ws.send(JSON.stringify({ migration_id: 'your-migration-id' }));
};
ws.onmessage = (e) => {
  const data = JSON.parse(e.data);
  console.log('📨 Message:', data);
};
ws.onerror = (e) => console.error('❌ Error:', e);
ws.onclose = () => console.log('🔌 Disconnected');
```

## Troubleshooting

### Backend Issues

**Problem: Import errors**
```bash
# Solution: Run from project root
cd s:\Programming\MigrateAI
python run_backend.py
```

**Problem: Port 8000 already in use**
```bash
# Find and kill process
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill
```

**Problem: Database errors**
```bash
# Delete database and restart
rm migrateai.db
python run_backend.py
```

**Problem: Module not found**
```bash
# Reinstall dependencies
pip install -r backend/requirements.txt
```

### Frontend Issues

**Problem: Cannot connect to backend**
- Check backend is running on port 8000
- Check CORS settings
- Verify proxy in `vite.config.js`

**Problem: WebSocket connection fails**
- Check backend WebSocket endpoint: `ws://localhost:8000/ws`
- Check browser console for errors
- Verify backend is running

**Problem: Components not appearing**
- Check browser console for errors
- Verify migration completed ingest/analyze phases
- Check WebSocket messages in Network tab

**Problem: Port 3000 already in use**
```bash
# Change port in vite.config.js or:
npm run dev -- --port 3001
```

### Common Issues

**Issue: "Migration not found"**
- Migration ID might be incorrect
- Check migration was created successfully
- Verify database exists

**Issue: "No components discovered"**
- Check demo_codebase path is correct
- Verify React files exist in the path
- Check backend logs for errors

**Issue: WebSocket messages not updating**
- Check WebSocket connection status
- Verify migration_id was sent correctly
- Check backend logs for WebSocket errors

## Verification Checklist

### Backend ✅
- [ ] Health endpoint returns 200
- [ ] Can start migration
- [ ] Migration status endpoint works
- [ ] WebSocket connects successfully
- [ ] Database created successfully

### Frontend ✅
- [ ] Loads at http://localhost:3000
- [ ] Shows "Connected" status
- [ ] Can start migration
- [ ] Components appear in file tree
- [ ] Logs stream in real-time
- [ ] Progress bar updates
- [ ] Diff viewer shows component code
- [ ] Pause button works

### Integration ✅
- [ ] Frontend receives WebSocket messages
- [ ] Real-time updates work
- [ ] Component discovery works
- [ ] Error handling works
- [ ] Full workflow completes

## Performance Testing

### Test Migration Speed

```bash
# Time the migration workflow
time curl -X POST http://localhost:8000/api/migrate/start \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "./demo_codebase"}'
```

### Monitor Resources

```bash
# Check backend process
# Windows: Task Manager
# Linux: htop or top

# Check frontend
# Browser DevTools → Performance tab
```

## Next Steps

Once basic testing passes:
1. Test with larger codebases
2. Test with actual Git repositories
3. Test error scenarios
4. Test with Gemini API (when implemented)
5. Test Docker test execution (Phase 2)
6. Test visual regression (Phase 2)

## Quick Test Script

Save as `quick_test.sh` (Linux/Mac) or `quick_test.ps1` (Windows):

**Windows PowerShell:**
```powershell
# Start backend
Start-Process python -ArgumentList "run_backend.py"

# Wait for backend
Start-Sleep -Seconds 3

# Test health
curl http://localhost:8000/health

# Start migration
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/migrate/start" -Method POST -ContentType "application/json" -Body '{"repo_url": "./demo_codebase"}'
Write-Host "Migration ID: $($response.migration_id)"

# Check status
Start-Sleep -Seconds 2
Invoke-RestMethod -Uri "http://localhost:8000/api/migrate/$($response.migration_id)"
```

**Linux/Mac:**
```bash
#!/bin/bash
# Start backend
python run_backend.py &
BACKEND_PID=$!

# Wait for backend
sleep 3

# Test health
curl http://localhost:8000/health

# Start migration
MIGRATION_RESPONSE=$(curl -X POST http://localhost:8000/api/migrate/start \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "./demo_codebase"}')

MIGRATION_ID=$(echo $MIGRATION_RESPONSE | jq -r '.migration_id')
echo "Migration ID: $MIGRATION_ID"

# Check status
sleep 2
curl http://localhost:8000/api/migrate/$MIGRATION_ID

# Cleanup
kill $BACKEND_PID
```

---

**Happy Testing! 🚀**

For issues or questions, check the logs in both terminal windows and browser console.
