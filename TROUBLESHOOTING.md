# Troubleshooting Guide

## "Nothing is happening" - Common Issues

### 1. Check Backend is Running
```bash
# Check if backend is running
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

### 2. Check WebSocket Connection
- Open browser console (F12)
- Look for "WebSocket connected" message
- If you see connection errors, check:
  - Backend is running on port 8000
  - No firewall blocking WebSocket connections
  - Try refreshing the page

### 3. Check Migration Status
The frontend now polls the backend every 2 seconds as a fallback. Check:
- Browser console for polling messages
- Network tab for API calls to `/api/migrate/{id}`

### 4. Check Repository Path
- **Local path**: Use absolute path like `s:\Programming\MigrateAI\demo_codebase`
- **Git URL**: Must be a valid GitHub URL like `https://github.com/user/repo`
- Check backend logs for "Repository accessed successfully" message

### 5. Check for React Files
- Backend logs should show: "Found X React files"
- If 0 files found:
  - Check the repository path is correct
  - Verify React files exist in the repo
  - Check backend console for errors

### 6. Check Database
- Database is created automatically on first run
- If issues persist, delete `migrateai.db` and restart backend
- Check backend console for database errors

## Debug Steps

### Step 1: Verify Backend
```bash
# Start backend and check for errors
python run_backend.py

# Look for:
# - "Application startup complete"
# - "✓ Added control_flags column" (first time only)
# - No import errors
```

### Step 2: Verify Frontend
```bash
cd frontend
npm run dev

# Check browser console for:
# - "WebSocket connected"
# - No CORS errors
# - No 404 errors
```

### Step 3: Test Migration
1. Enter repository URL/path
2. Click "Start Migration"
3. Check browser console for:
   - "Migration started with ID: ..."
   - WebSocket messages
   - Polling requests (every 2 seconds)

### Step 4: Check Backend Logs
Look for:
- "Starting ingestion for ..."
- "Repository accessed successfully at: ..."
- "Found X React files"
- "Found X class components"
- Any error messages

## Common Error Messages

### "Failed to ingest repository"
- **Cause**: Invalid path or git clone failed
- **Fix**: Check repository path/URL is correct

### "No React files found"
- **Cause**: Repository doesn't contain React files or path is wrong
- **Fix**: Verify repository path and that it contains .jsx/.js files

### "No class components found"
- **Cause**: All components are already functional or no components exist
- **Fix**: This is normal if the codebase has no class components

### "WebSocket connection failed"
- **Cause**: Backend not running or WebSocket issues
- **Fix**: Restart backend, check firewall, try refreshing page

### "Cannot pause migration with status: completed"
- **Cause**: Migration already finished
- **Fix**: Start a new migration

## Status Polling Fallback

The frontend now polls the backend every 2 seconds if WebSocket fails. This ensures:
- Status updates are received even if WebSocket is unstable
- Components are discovered even if WebSocket messages are missed
- Progress is updated regularly

Check browser Network tab for:
- `GET /api/migrate/{migration_id}` requests every 2 seconds
- These should return migration status

## Still Not Working?

1. **Check Backend Console**: Look for Python errors or exceptions
2. **Check Browser Console**: Look for JavaScript errors
3. **Check Network Tab**: Look for failed API requests
4. **Try Demo Codebase**: Use `./demo_codebase` or absolute path to test
5. **Restart Both**: Stop and restart both backend and frontend

## Enable Debug Logging

Add to backend `main.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show detailed logs of what's happening.
