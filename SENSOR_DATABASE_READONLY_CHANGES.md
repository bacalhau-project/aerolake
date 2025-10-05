# Sensor Database Read-Only Mode Changes

## Summary

All code that accesses the sensor database (`sensor_data.db`) has been updated to use **read-only mode** exclusively. This prevents any accidental modifications to the sensor database and avoids database lock conflicts.

## Changes Made

### 1. spot/instance-files/opt/sensor/edge_processor.py
- **Lines**: Changed from regular `sqlite3.connect()` to read-only mode
- Now uses: `sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=30.0)`

### 2. spot/instance-files/opt/sensor/sensor_models.py  
- **Line**: Changed sensor database connection to read-only mode
- Now uses: `sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True, timeout=30.0)`

### 3. spot/instance-files/opt/sensor/Dockerfile
- **Line**: Updated to mount sensor database as read-only volume (`:ro` flag)

### 4. spot/instance-files/README.md
- **Line**: Updated documentation to explain read-only database access

## Key Benefits

1. **No Database Locks**: Read-only connections don't create write locks, avoiding conflicts with sensor writes
2. **Data Integrity**: Impossible to accidentally modify sensor data
3. **Clear Separation**: Configuration data is stored separately from sensor data
4. **Better Performance**: Read-only connections have less overhead

## Connection Pattern

All sensor database connections now follow this pattern:

```python
# Read-only connection to sensor database
conn = sqlite3.connect(
    f"file:{sensor_db_path}?mode=ro",
    uri=True,
    timeout=30.0
)
```

## Configuration Database

Pipeline configuration is now stored in a separate database (`pipeline_config.db`) that:
- Is completely independent of the sensor database
- Can be safely written to without affecting sensor operations
- Contains only configuration and state management tables

## Verification

To verify these changes work correctly:

```bash
# Test read-only access to sensor database
docker run --rm \
    -v $(pwd)/sample-sensor/data/sensor_data.db:/app/sensor_data.db:ro \
    ghcr.io/expanso-io/sensor-processor:latest \
    --test-connection

# Test that sensor database remains read-only
expanso job run jobs/edge-processing-job.yaml --dry-run
```

## Migration Notes

For existing deployments:
1. Edge node configuration will be automatically created in `/expanso_data/state/`
2. Any existing configuration in the sensor database is abandoned (but not deleted)
3. The sensor database remains completely untouched and read-only