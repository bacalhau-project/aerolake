# Pipeline Redesign for Demo Requirements

## Current vs Proposed Pipeline Modes

### Proposed Pipeline Mode Behaviors:

| Stage | Mode Name | Behavior | Target Buckets | Demo Purpose |
|-------|-----------|----------|----------------|--------------|
| 1 | `raw` | Line-by-line ingestion, no processing | ingestion | Show raw data capture |
| 2 | `validated` | Apply basic sensor validation rules | validated + anomalies (split) | Show validation splitting |
| 3 | `schematized` | Transform to wind turbine schema + external JSON validation | schematized + anomalies (split) | Show schema transformation |
| 4 | `aggregated` | Time-window aggregations of valid data only | aggregated | Show analytics processing |
| 5 | `anomaly_aggregated` | Aggregations with anomaly detection and exclusion | aggregated + anomalies (split) | Show smart aggregation |

## Implementation Changes Required

### 1. Fix Uploader Validation Logic (`sqlite_to_databricks_uploader.py`)

```python
def _validate_and_split_data(self, data):
    valid_records = []
    invalid_records = []
    
    if self.current_pipeline_type == "raw":
        # No validation, all records are "valid"
        return data, []
    
    elif self.current_pipeline_type == "validated":
        # Basic sensor validation (temperature, humidity ranges)
        for record in data:
            if self._validate_sensor_ranges(record):
                valid_records.append(record)
            else:
                invalid_records.append(record)
    
    elif self.current_pipeline_type == "schematized":
        # Transform to wind turbine schema + external validation
        schema = self._fetch_external_schema()  # New method
        for record in data:
            turbine_record = self._map_to_turbine_schema(record)
            if self._validate_against_schema(turbine_record, schema):
                valid_records.append(turbine_record)
            else:
                invalid_records.append(turbine_record)
    
    elif self.current_pipeline_type == "aggregated":
        # Only process valid records for aggregation
        for record in data:
            if self._validate_sensor_ranges(record):
                valid_records.append(self._aggregate_record(record))
    
    elif self.current_pipeline_type == "anomaly_aggregated":
        # Aggregate with anomaly detection
        for record in data:
            if self._validate_sensor_ranges(record):
                if not self._detect_anomaly(record):
                    valid_records.append(self._aggregate_record(record))
                else:
                    invalid_records.append(record)
    
    return valid_records, invalid_records
```

### 2. Add External Schema Fetching

```python
def _fetch_external_schema(self):
    """Fetch schema from GitHub or hosted URL"""
    schema_url = self.config.get('external_schema_url', 
        'https://raw.githubusercontent.com/your-org/schemas/main/wind-turbine-schema.json')
    
    try:
        response = requests.get(schema_url, timeout=10)
        return response.json()
    except:
        # Fallback to local schema
        with open('wind-turbine-schema.json') as f:
            return json.load(f)
```

### 3. Update Pipeline-to-Bucket Mapping

```python
self.pipeline_bucket_map = {
    "raw": "ingestion",
    "validated": "SPLIT",  # Special handling - splits to validated/anomalies
    "schematized": "SPLIT",  # Splits to schematized/anomalies  
    "aggregated": "aggregated",
    "anomaly_aggregated": "SPLIT"  # Splits to aggregated/anomalies
}
```

### 4. Unity Catalog Views (No New Tables!)

Create views in Databricks to filter existing tables:

```sql
-- View for valid sensor readings only
CREATE OR REPLACE VIEW sensor_readings_valid_only AS
SELECT * FROM sensor_readings_validated
WHERE anomaly_flag = 0;

-- View for aggregations excluding anomalies
CREATE OR REPLACE VIEW sensor_readings_clean_aggregated AS
SELECT * FROM sensor_readings_aggregated
WHERE sensor_id NOT IN (
    SELECT DISTINCT sensor_id 
    FROM sensor_readings_anomalies 
    WHERE timestamp > current_timestamp() - INTERVAL 1 HOUR
);

-- View for recent anomalies with context
CREATE OR REPLACE VIEW sensor_readings_anomaly_context AS
SELECT 
    a.*,
    v.temperature as prev_temp,
    v.humidity as prev_humidity
FROM sensor_readings_anomalies a
LEFT JOIN sensor_readings_validated v
ON a.sensor_id = v.sensor_id 
AND v.timestamp < a.timestamp
AND v.timestamp > a.timestamp - INTERVAL 5 MINUTES;
```

## Demo Script Flow

```bash
# Stage 1: Raw ingestion (1 min)
./scripts/run-pipeline-demo.sh raw
# Shows: Line-by-line data → ingestion bucket

# Stage 2: Basic validation (1 min)  
./scripts/run-pipeline-demo.sh validated
# Shows: Valid → validated bucket, Invalid → anomalies bucket

# Stage 3: Schema transformation with external JSON (1 min)
./scripts/run-pipeline-demo.sh schematized  
# Shows: Fetches GitHub schema, transforms, validates, splits

# Stage 4: Aggregation of clean data (1 min)
./scripts/run-pipeline-demo.sh aggregated
# Shows: Only valid data aggregated → aggregated bucket

# Stage 5: Smart aggregation with anomaly exclusion (1 min)
./scripts/run-pipeline-demo.sh anomaly_aggregated
# Shows: Aggregates clean data, routes anomalies separately
```

## Benefits of This Approach

1. **No new buckets needed** - Uses existing 7 buckets
2. **No new Unity Catalog tables** - Uses views for filtering
3. **Clear progression** - Each stage builds on the previous
4. **Demonstrates key concepts**:
   - Raw ingestion
   - Validation splitting
   - External schema integration
   - Smart aggregation with anomaly handling
5. **Minimal code changes** - Mostly fixing existing validation logic

## Next Steps

1. Update `sqlite_to_databricks_uploader.py` with fixed validation logic
2. Add external schema fetching capability
3. Create Unity Catalog views for filtered data
4. Update demo script with new `anomaly_aggregated` mode
5. Test end-to-end pipeline with all 5 stages