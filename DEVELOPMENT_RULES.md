# Development and Cleanup Rules

## File Cleanup Guidelines

### ✅ SAFE TO DELETE (Development Artifacts)
These files/directories can always be safely removed during cleanup:

**IDE and Editor Files:**
- `.vscode/`, `.cursor/`, `.idea/`
- `.aiderignore`, editor-specific configs

**Build and Cache Files:**
- `.ruff_cache/`, `.mypy_cache/`, `__pycache__/`
- `node_modules/`, `.specstory/`
- `.DS_Store`, system-generated files

**Development Environment:**
- `.venv/`, `venv/`, `ENV/`
- `.env.local`, `.env.development`
- Development-only log files in `logs/` directories

**Test Artifacts:**
- `test-*.sh`, `debug-*.py`, `fix-*.py`
- Temporary test configuration files
- Development database files (`.db`, `.db-wal`, `.db-shm`) in dev directories

### ❌ NEVER DELETE (Deployment Required)
These files must NEVER be deleted, even during cleanup:

**Deployment Configuration:**
- `spot/instance-files/etc/bacalhau/orchestrator_endpoint`
- `spot/instance-files/etc/bacalhau/orchestrator_token`
- `spot/instance-files/etc/aws/credentials/` (any actual credential files)
- `spot/instances.json` (if it exists with real instance data)

**Service Configuration:**
- `spot/instance-files/opt/sensor/config/sensor-config.yaml`
- Any `.service` files in `systemd/system/`
- Docker compose files for actual services

**Production Data:**
- Any database files in production paths (`/opt/`, `/etc/`)
- State directories with operational data
- Log files that contain deployment history

**Credential Files:**
- Any file ending in `-credentials`, `.pem`, `.key`
- AWS credential files (even if development)
- API keys, tokens, certificates

### 🔍 CLEANUP DECISION PROCESS

Before deleting ANY file, ask:

1. **Is this a development artifact?** (IDE, cache, test) → Safe to delete
2. **Is this required for deployment?** (config, credentials, state) → NEVER delete
3. **Does it contain operational data?** (logs, databases, state) → NEVER delete
4. **When in doubt** → Don't delete, ask the user

### 📝 .gitignore vs Cleanup

**Important distinction:**
- **`.gitignore`**: Prevents files from being committed to git
- **Cleanup**: Removes files from filesystem

A file can be:
- In `.gitignore` but required for deployment (keep on filesystem)
- Safe to delete and should be in `.gitignore` (remove from filesystem)

**Rule**: Files in `.gitignore` are NOT automatically safe to delete!

### 🚨 Recovery Process

If deployment files are accidentally deleted:
1. Check if they're in git history (restore with `git checkout`)
2. Recreate from `.sample` templates if available
3. Ask user for the correct values
4. Document the incident to improve this rule set