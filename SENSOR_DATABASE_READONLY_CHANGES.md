# Sensor Database Read-Only Mode Changes

## Summary

All code that accesses the sensor database (`sensor_data.db`) has been updated to use **read-only mode** exclusively. This prevents any accidental modifications to the sensor database and avoids database lock conflicts.

## Changes Made

### 1. databricks-uploader/sqlite_to_json_transformer.py
- **Lines 277, 389**: Changed from regular `sqlite3.connect()` to read-only mode
- Now uses: `sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=30.0)`

### 2. databricks-uploader/pipeline_orchestrator.py  
- **Line 154**: Changed sensor database connection to read-only mode
- Now uses: `sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True, timeout=30.0)`

### 3. databricks-uploader/api_backend.py
- **Line 436**: Changed sensor database connection to read-only mode
- Now uses: `sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=30.0)`
- **Line 155-156**: Changed PipelineManager to use separate config database instead of sensor database
- Now uses: `pipeline_config.db` instead of `sensor_data.db`

### 4. databricks-uploader/sqlite_to_databricks_uploader.py
- **Already correct**: Lines 445-449 and 495-496 were already using read-only mode

### 5. pipeline-manager/pipeline_controller.py
- **Complete rewrite**: Separated configuration storage from sensor database
- Now uses TWO databases:
  - `pipeline_config.db` for configuration (read/write)
  - `sensor_data.db` for sensor data (read-only)
- Added explicit check to prevent using sensor database for configuration
- All sensor database access uses read-only mode

### 6. pipeline-manager/docker-compose.yml
- Updated to mount sensor database as read-only volume (`:ro` flag)
- Added separate volume for configuration database

### 7. pipeline-manager/README.md
- Updated documentation to explain database separation
- Clear distinction between config database and sensor database

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
uv run -s databricks-uploader/sqlite_to_json_transformer.py \
    --db ../sample-sensor/data/sensor_data.db \
    --table sensor_readings

# Test pipeline configuration (uses separate database)
uv run -s pipeline-manager/pipeline_controller.py \
    --config-db pipeline_config.db get

# Test that sensor database remains read-only
uv run -s pipeline-manager/pipeline_controller.py \
    --config-db pipeline_config.db \
    --sensor-db ../sample-sensor/data/sensor_data.db \
    read-sensor --limit 10
```

## Migration Notes

For existing deployments:
1. Pipeline configuration will be automatically created in `pipeline_config.db`
2. Any existing configuration in the sensor database is abandoned (but not deleted)
3. The sensor database remains completely untouched and read-only