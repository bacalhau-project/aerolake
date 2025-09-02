# Pipeline Manager

Atomic pipeline configuration management for the Databricks S3 uploader pipeline.

## Overview

This container provides atomic read/write operations for managing pipeline configuration in a **SEPARATE** configuration database. This ensures the sensor database remains **READ-ONLY** for all tools.

Key features:
- Uses a separate `pipeline_config.db` database for configuration
- Sensor database is accessed in **read-only mode** only
- WAL (Write-Ahead Logging) mode for better concurrency
- IMMEDIATE transactions for write operations
- Retry logic with exponential backoff for locked database scenarios
- Proper transaction isolation

## Important: Database Separation

**The pipeline manager now uses TWO separate databases:**
1. `pipeline_config.db` - For storing pipeline configuration (read/write)
2. `sensor_data.db` - The sensor database (read-only access)

This separation ensures that the sensor database remains untouched and read-only for all our tools.

## Usage

### Local Development

```bash
# View current pipeline configuration
uv run -s pipeline_controller.py --config-db pipeline_config.db get

# Change pipeline type
uv run -s pipeline_controller.py --config-db pipeline_config.db set filtered \
    --by "operations" --reason "Enabling anomaly filtering"

# View history
uv run -s pipeline_controller.py --config-db pipeline_config.db history --limit 20

# Monitor changes in real-time
uv run -s pipeline_controller.py --config-db pipeline_config.db monitor

# Read sensor data (read-only mode)
uv run -s pipeline_controller.py --config-db pipeline_config.db \
    --sensor-db ../sample-sensor/data/sensor_data.db read-sensor --limit 10
```

### Docker Usage

```bash
# Build the container
docker-compose build

# View current pipeline
docker-compose run --rm pipeline-manager python pipeline_controller.py \
    --config-db /data/pipeline_config.db get

# Change pipeline type
docker-compose run --rm pipeline-manager python pipeline_controller.py \
    --config-db /data/pipeline_config.db set filtered --by "docker_user"

# View history
docker-compose run --rm pipeline-manager python pipeline_controller.py \
    --config-db /data/pipeline_config.db history

# Monitor changes
docker-compose run --rm pipeline-manager python pipeline_controller.py \
    --config-db /data/pipeline_config.db monitor
```

### Kubernetes Usage

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: set-pipeline-config
spec:
  template:
    spec:
      containers:
      - name: pipeline-manager
        image: pipeline-manager:latest
        command: ["python", "pipeline_controller.py"]
        args: 
          - "--config-db"
          - "/data/pipeline_config.db"
          - "set"
          - "aggregated"
          - "--by"
          - "k8s_admin"
          - "--reason"
          - "Enable aggregation pipeline"
        volumeMounts:
        - name: config-volume
          mountPath: /data
      volumes:
      - name: config-volume
        persistentVolumeClaim:
          claimName: pipeline-config-pvc
```

## Pipeline Types

- `raw`: Process all sensor data without filtering
- `filtered`: Apply anomaly detection and filtering
- `aggregated`: Aggregate data before processing
- `anomaly`: Focus on anomaly detection and alerting

## Database Access Patterns

### Configuration Database (pipeline_config.db)
- **Access Mode**: Read/Write
- **Location**: Separate from sensor database
- **Purpose**: Store pipeline configuration and history
- **Tables**: `pipeline_config`

### Sensor Database (sensor_data.db)
- **Access Mode**: READ-ONLY
- **Location**: Managed by sensor system
- **Purpose**: Read sensor data for processing
- **Connection**: Uses SQLite URI with `?mode=ro` flag

## Example: Integration with Uploader

The uploader can read the pipeline configuration to determine processing mode:

```python
from pipeline_controller import PipelineController

# Use separate configuration database
controller = PipelineController("pipeline_config.db")
config = controller.get_current_pipeline()

if config['pipeline_type'] == 'filtered':
    # Apply filtering logic
    pass
elif config['pipeline_type'] == 'aggregated':
    # Apply aggregation logic
    pass
```

## Monitoring

The monitor command provides real-time visibility into configuration changes:

```bash
docker-compose run --rm pipeline-manager python pipeline_controller.py \
    --config-db /data/pipeline_config.db monitor
```

This will display:
- Current pipeline type
- Last update timestamp
- Who made the change
- Reason for the change
- Live updates when configuration changes

## Security Notes

1. The sensor database is NEVER modified by this tool
2. All sensor database connections use read-only mode (`?mode=ro`)
3. Configuration is stored in a separate database
4. Proper transaction isolation prevents race conditions
5. WAL mode enables concurrent readers