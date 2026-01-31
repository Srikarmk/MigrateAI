# Backend Import Structure Fixes

## Issue
The backend code was using absolute imports (`from backend.models import ...`) which assumes the project root is in PYTHONPATH. This can cause import errors depending on how the code is run.

## Solution
Changed all internal backend imports to use **relative imports** within the backend package:

### Changes Made

1. **backend/main.py**
   - Changed: `from backend.models import ...` → `from .models import ...`
   - Changed: `from backend.state import ...` → `from .state import ...`
   - Changed: `from backend.agents.ingest import ...` → `from .agents.ingest import ...`

2. **backend/agents/analyze.py**
   - Changed: `from backend.models import ...` → `from ..models import ...`

### Import Patterns

- **Within backend package**: Use `.` (e.g., `from .models import ...`)
- **From agents subpackage**: Use `..` to go up one level (e.g., `from ..models import ...`)
- **Within agents**: Use `.` (e.g., `from .ingest import ...`)

## Running the Backend

### Recommended: From Project Root
```bash
# Option 1: Using uvicorn
uvicorn backend.main:app --reload

# Option 2: Using helper script
python run_backend.py

# Option 3: As Python module
python -m backend.main
```

### Why This Works
- When running as a module (`python -m backend.main`), Python treats `backend` as a package
- Relative imports work correctly within the package structure
- The project root is automatically in the Python path

### File Structure
```
MigrateAI/
├── backend/
│   ├── __init__.py          # Makes backend a package
│   ├── main.py              # Uses: from .models import ...
│   ├── models.py
│   ├── state.py
│   ├── websocket_manager.py
│   └── agents/
│       ├── __init__.py      # Makes agents a subpackage
│       ├── ingest.py
│       ├── analyze.py       # Uses: from ..models import ...
│       └── ...
├── run_backend.py           # Helper script
└── requirements.txt
```

## Verification

All imports now use relative paths:
- ✅ `backend/main.py` → `from .models import ...`
- ✅ `backend/agents/analyze.py` → `from ..models import ...`
- ✅ No absolute `backend.*` imports within backend package

## Benefits

1. **Portable**: Works regardless of where Python is run from
2. **Standard**: Follows Python package best practices
3. **Clear**: Makes package structure explicit
4. **Compatible**: Works with both direct execution and module execution
