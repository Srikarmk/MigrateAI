# Changelog - Pause/Resume/Stop & GitHub URL Fix

## Changes Made

### 1. Added Pause/Resume/Stop Functionality

#### Backend Changes:
- **New File**: `backend/migration_control.py`
  - Migration control system with pause/resume/stop flags
  - Uses asyncio Events for proper async pause/resume handling

- **Updated**: `backend/models.py`
  - Added `PAUSED` and `STOPPED` status to `MigrationStatus` enum

- **Updated**: `backend/state.py`
  - Added `control_flags` column to `MigrationRecord` model
  - Updated `_record_to_dict` to include control_flags

- **Updated**: `backend/main.py`
  - Added pause/resume/stop endpoints:
    - `POST /api/migrate/pause?migration_id={id}`
    - `POST /api/migrate/resume?migration_id={id}`
    - `POST /api/migrate/stop?migration_id={id}`
  - Updated `run_migration_workflow` to check for pause/stop flags
  - Added proper error handling for git cloning

#### Frontend Changes:
- **Updated**: `frontend/src/App.jsx`
  - Added `handleResumeMigration` function
  - Added `handleStopMigration` function
  - Updated UI to show:
    - **Pause** and **Stop** buttons when status is "running"
    - **Resume** and **Stop** buttons when status is "paused"

### 2. Fixed GitHub URL Handling

#### Backend Changes:
- **Updated**: `backend/agents/ingest.py`
  - Improved git URL detection (handles `github.com` URLs without `https://`)
  - Better error messages for failed cloning
  - Handles branch checkout more robustly
  - Normalizes GitHub URLs (adds `.git` if missing, adds `https://` if missing)

## How It Works

### Pause/Resume/Stop Flow:

1. **Pause**:
   - Sets pause flag in migration control
   - Updates database status to "paused"
   - Workflow checks pause flag at each step and waits if paused

2. **Resume**:
   - Clears pause flag
   - Workflow continues from where it left off
   - Updates status back to "running"

3. **Stop**:
   - Sets stop flag
   - Workflow checks stop flag and exits gracefully
   - Updates database status to "stopped"
   - Cleans up resources

### GitHub URL Handling:

The system now handles various GitHub URL formats:
- `https://github.com/user/repo`
- `github.com/user/repo`
- `https://github.com/user/repo.git`
- `git@github.com:user/repo.git`

## Testing

### Test Pause/Resume:
1. Start a migration
2. Click "Pause" button
3. Status should change to "paused"
4. Click "Resume" button
5. Migration should continue

### Test Stop:
1. Start a migration
2. Click "Stop" button
3. Status should change to "stopped"
4. Migration should not continue

### Test GitHub URL:
1. Enter: `https://github.com/Srikarmk/Salescope`
2. Click "Start Migration"
3. Should clone the repository successfully
4. Should find React components (if any)

## API Endpoints

### Pause Migration
```bash
POST /api/migrate/pause?migration_id={migration_id}
```

### Resume Migration
```bash
POST /api/migrate/resume?migration_id={migration_id}
```

### Stop Migration
```bash
POST /api/migrate/stop?migration_id={migration_id}
```

## Database Migration

If you have an existing database, you may need to:
1. Delete `migrateai.db` and let it recreate
2. Or manually add the `control_flags` column

The new column will be added automatically on next startup for new databases.

## Notes

- Pause/Resume works at workflow step boundaries (between agents)
- Stop immediately halts the workflow
- GitHub URLs are normalized automatically
- Better error messages for git cloning failures
