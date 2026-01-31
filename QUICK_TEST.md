# Quick Test Reference

## 🚀 Quick Start

### Start Both Services

**Terminal 1 - Backend:**
```bash
python run_backend.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Browser:**
```
http://localhost:3000
```

## ✅ Health Checks

### Backend Health
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

### Frontend
- Open: http://localhost:3000
- Check: Connection status shows "Connected" (green)

## 🧪 Test Migration

### Via Frontend UI
1. Enter: `./demo_codebase`
2. Click: "Start Migration"
3. Watch: Real-time updates

### Via API
```bash
curl -X POST http://localhost:8000/api/migrate/start \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "./demo_codebase"}'
```

## 📋 Common Test Commands

### Get Migration Status
```bash
curl http://localhost:8000/api/migrate/{migration_id}
```

### Get Component Diff
```bash
curl http://localhost:8000/api/diff/Counter.jsx
```

### Pause Migration
```bash
curl -X POST "http://localhost:8000/api/migrate/pause?migration_id={migration_id}"
```

## 🔍 Debugging

### Check Backend Logs
- Look at Terminal 1 (backend) for errors

### Check Frontend Logs
- Open Browser DevTools (F12)
- Check Console tab
- Check Network tab for API calls

### Check WebSocket
```javascript
// Browser Console
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| Port 8000 in use | Kill process or change port |
| Port 3000 in use | Change port in vite.config.js |
| Import errors | Run from project root |
| WebSocket not connecting | Check backend is running |
| No components found | Check path is correct |

## 📊 Expected Results

### Demo Codebase Should Find:
- ✅ Counter.jsx
- ✅ UserProfile.jsx
- ✅ Timer.jsx
- ✅ ContactForm.jsx
- ✅ DataFetcher.jsx

### Migration Flow:
1. Ingest (0-20%)
2. Analyze (20-40%)
3. Plan (40-60%)
4. Execute (60-70%) - Placeholder
5. Test (70-80%) - Placeholder
6. Verify (80-90%) - Placeholder
7. Review (90-95%) - Placeholder
8. Document (95-100%) - Placeholder

---

**Full guide:** See `TESTING_GUIDE.md`
