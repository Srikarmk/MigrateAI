# Database Schema Fix

## Issue
The database was missing the `control_flags` column, causing errors when starting migrations.

## Solution
Added automatic database migration that:
1. Checks if `control_flags` column exists
2. Adds it if missing
3. Handles backward compatibility

## What to Do

### Option 1: Automatic (Recommended)
Just restart the backend - it will automatically add the missing column:
```bash
python run_backend.py
```

You should see: `✓ Added control_flags column to migrations table`

### Option 2: Manual Fix
If automatic migration doesn't work, delete the database and let it recreate:
```bash
# Stop the backend
# Delete the database file
rm migrateai.db  # Linux/Mac
del migrateai.db  # Windows

# Restart backend - it will create a fresh database
python run_backend.py
```

## What Changed

1. **state.py**: Added `_migrate_control_flags()` function that runs on startup
2. **MigrationRecord**: Made `control_flags` nullable for backward compatibility
3. **create_migration**: Sets default control_flags when creating new migrations
4. **_record_to_dict**: Handles missing control_flags gracefully

The system now works with both old and new database schemas!
