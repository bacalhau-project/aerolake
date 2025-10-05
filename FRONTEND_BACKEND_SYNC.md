# Frontend Dashboard & Databricks Pipeline Integration Guide

## Overview
This document explains how the demo dashboard frontend (specified in FRONT_END_SPEC.md) connects to and visualizes data from the Databricks pipeline backend.

## Data Flow Architecture

### Backend Pipeline (Current Implementation)
```
Wind Turbine Sensors → SQLite DB → JSON Transformer → S3 Upload → Databricks Unity Catalog
                                         ↓
                              Schema Validation (wind-turbine-schema.json)
                                         ↓
                              Databricks Tables (Bronze/Silver/Gold layers)
```

### Frontend Integration Points

## 1. Databricks Tables Structure

Based on the backend code, these are the Unity Catalog tables the frontend should query:

### Bronze Layer (Raw Data)
- **Table**: `sensor_data_bronze`
- **Location**: Unity Catalog path configured in Databricks notebooks
- **Schema**: Raw JSON data from sensors
- **Update Frequency**: Real-time as sensors push data

### Silver Layer (Schematized Data)
- **Table**: `sensor_data_silver`
- **Schema**: Validated against `wind-turbine-schema.json`
- **Fields** (from schema):
  ```json
  {
    "timestamp": "string (ISO 8601)",
    "sensor_id": "string",
    "location": {
      "latitude": "number",
      "longitude": "number",
      "city": "string",
      "state": "string",
      "country": "string"
    },
    "wind_speed": "number (m/s)",
    "wind_direction": "number (degrees)",
    "power_output": "number (kW)",
    "temperature": "number (Celsius)",
    "humidity": "number (percentage)",
    "blade_pitch_angle": "number (degrees)",
    "rotor_speed": "number (RPM)",
    "generator_temp": "number (Celsius)",
    "nacelle_position": "number (degrees)",
    "vibration_level": "number",
    "status": "string (operational/maintenance/fault)",
    "anomaly_detected": "boolean",
    "anomaly_score": "number (0-1)",
    "maintenance_required": "boolean"
  }
  ```

### Gold Layer (Aggregated Data)
- **Table**: `sensor_data_aggregated`
- **Aggregations**: Hourly/Daily summaries
- **Metrics**: Average power output, efficiency, anomaly counts

## 2. API Endpoints to Implement

The frontend expects these endpoints. Here's how they map to Databricks:

### Sensor Status Endpoints
```python
# /api/sensors/status
# Query: SELECT DISTINCT sensor_id, location, status, MAX(timestamp) as last_reading
#        FROM sensor_data_silver
#        GROUP BY sensor_id, location, status

# /api/sensors/realtime
# Query: SELECT * FROM sensor_data_silver
#        WHERE timestamp > NOW() - INTERVAL 1 MINUTE
#        ORDER BY timestamp DESC

# /api/sensors/:id/history
# Query: SELECT timestamp, power_output, wind_speed, temperature
#        FROM sensor_data_silver
#        WHERE sensor_id = :id
#        AND timestamp > NOW() - INTERVAL 24 HOURS
```

### Pipeline Data Endpoints
```python
# /api/pipeline/raw
# Query: SELECT * FROM sensor_data_bronze
#        ORDER BY timestamp DESC
#        LIMIT 50

# /api/pipeline/schematized
# Query: SELECT * FROM sensor_data_silver
#        ORDER BY timestamp DESC
#        LIMIT 50

# /api/pipeline/anomalies
# Query: SELECT * FROM sensor_data_silver
#        WHERE anomaly_detected = true
#        ORDER BY anomaly_score DESC, timestamp DESC
#        LIMIT 50

# /api/pipeline/aggregated
# Query: SELECT * FROM sensor_data_aggregated
#        WHERE window_start > NOW() - INTERVAL 1 HOUR
```

### Statistics Endpoints
```python
# /api/stats/throughput
# Query: SELECT COUNT(*) as records_per_second
#        FROM sensor_data_bronze
#        WHERE timestamp > NOW() - INTERVAL 1 SECOND

# /api/stats/latency
# Query: SELECT AVG(processing_time_ms) as avg_latency
#        FROM data_pipeline_metrics
#        WHERE timestamp > NOW() - INTERVAL 5 MINUTES
```

## 3. Data Mapping Guide

### Frontend "Sensors" → Backend "Wind Turbines"
```javascript
// Frontend expects
{
  id: string,
  location: { lat, lng, city },
  temperature: number,
  humidity: number,
  pressure: number,  // Map from generator_temp or ambient pressure
  status: 'active' | 'warning' | 'critical' | 'offline',
  lastReading: Date,
  trend: 'up' | 'down' | 'stable',
  history: Array
}

// Backend provides
{
  sensor_id: string,
  location: { latitude, longitude, city, state, country },
  temperature: number,  // Celsius - convert to Fahrenheit for US demos
  humidity: number,
  generator_temp: number,  // Can be used as "pressure" proxy
  status: 'operational' | 'maintenance' | 'fault',
  timestamp: string,
  power_output: number  // Use for trend calculation
}
```

### Status Mapping
```javascript
const statusMap = {
  'operational': 'active',
  'maintenance': 'warning',
  'fault': 'critical',
  'offline': 'offline'  // When no recent data
};
```

### Anomaly Detection Mapping
- Backend `anomaly_detected: true` → Frontend purple markers
- Backend `anomaly_score > 0.7` → Frontend "critical" status
- Backend `maintenance_required: true` → Frontend "warning" status

## 4. Real-time Data Synchronization

### Current Backend Capabilities
- **sqlite_to_databricks_uploader.py**: Pushes data to Databricks
- **pipeline_orchestrator.py**: Manages data flow
- **databricks-notebooks/setup-and-run-autoloader.py**: Auto-ingests new data

### Frontend Polling Strategy
```javascript
// Poll Databricks SQL Warehouse endpoint
const DATABRICKS_API = process.env.DATABRICKS_HOST;
const WAREHOUSE_ID = process.env.SQL_WAREHOUSE_ID;

// Use Databricks SQL REST API
async function queryDatabricks(sql) {
  const response = await fetch(`${DATABRICKS_API}/api/2.0/sql/statements`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${DATABRICKS_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      warehouse_id: WAREHOUSE_ID,
      statement: sql,
      wait_timeout: '10s'
    })
  });
  return response.json();
}
```

## 5. Mock Data Generation

When Databricks is unavailable, generate mock data matching the wind turbine schema:

```javascript
function generateMockSensorData() {
  return {
    sensor_id: `WT-${Math.floor(Math.random() * 1000)}`,
    timestamp: new Date().toISOString(),
    location: {
      latitude: 32.7157 + (Math.random() - 0.5) * 10,
      longitude: -117.1611 + (Math.random() - 0.5) * 10,
      city: ['Dallas', 'Austin', 'Houston', 'Phoenix'][Math.floor(Math.random() * 4)],
      state: 'TX',
      country: 'USA'
    },
    wind_speed: 5 + Math.random() * 20,
    power_output: 500 + Math.random() * 3500,
    temperature: 15 + Math.random() * 20,
    humidity: 40 + Math.random() * 40,
    rotor_speed: 10 + Math.random() * 20,
    generator_temp: 40 + Math.random() * 40,
    vibration_level: Math.random() * 2,
    status: Math.random() > 0.95 ? 'maintenance' : 'operational',
    anomaly_detected: Math.random() > 0.95,
    anomaly_score: Math.random() * 0.3,
    maintenance_required: Math.random() > 0.98
  };
}
```

## 6. Implementation Checklist for Frontend Developer

### Prerequisites
- [ ] Get Databricks workspace URL from backend team
- [ ] Get SQL Warehouse ID from backend team
- [ ] Get Databricks personal access token
- [ ] Understand Unity Catalog namespace (catalog.schema.table)

### Environment Variables Needed
```env
VITE_DATABRICKS_HOST=https://xxx.cloud.databricks.com
VITE_SQL_WAREHOUSE_ID=xxx
VITE_DATABRICKS_TOKEN=dapi...
VITE_CATALOG_NAME=wind_turbine_catalog
VITE_SCHEMA_NAME=sensor_data
```

### API Implementation Order
1. Start with mock data only (no Databricks connection)
2. Implement `/api/sensors/status` using Databricks SQL REST API
3. Add real-time polling for `/api/sensors/realtime`
4. Implement anomaly detection queries
5. Add aggregation queries for analytics views

### Data Transformation Pipeline
```javascript
// Transform Databricks wind turbine data to frontend sensor format
function transformWindTurbineToSensor(turbineData) {
  return {
    id: turbineData.sensor_id,
    location: {
      lat: turbineData.location.latitude,
      lng: turbineData.location.longitude,
      city: turbineData.location.city
    },
    temperature: turbineData.temperature * 9/5 + 32, // C to F
    humidity: turbineData.humidity,
    pressure: turbineData.generator_temp, // Proxy metric
    status: mapStatus(turbineData),
    lastReading: new Date(turbineData.timestamp),
    trend: calculateTrend(turbineData.power_output),
    history: [] // Populate from historical query
  };
}

function mapStatus(turbineData) {
  if (turbineData.anomaly_score > 0.7) return 'critical';
  if (turbineData.maintenance_required) return 'warning';
  if (turbineData.status === 'fault') return 'critical';
  if (turbineData.status === 'maintenance') return 'warning';
  if (turbineData.status === 'operational') return 'active';
  return 'offline';
}
```

## 7. Testing Integration

### Scripts to Verify Connection
```python
# scripts/test-frontend-queries.py
#!/usr/bin/env python3
# /// script
# dependencies = [
#   "databricks-sql-connector",
#   "python-dotenv",
# ]
# ///

import os
from databricks import sql
from dotenv import load_dotenv

load_dotenv()

# Test queries that frontend will use
queries = [
    "SELECT COUNT(*) FROM sensor_data_silver",
    "SELECT * FROM sensor_data_silver LIMIT 5",
    "SELECT COUNT(*) FROM sensor_data_silver WHERE anomaly_detected = true",
    "SELECT sensor_id, MAX(timestamp) FROM sensor_data_silver GROUP BY sensor_id"
]

connection = sql.connect(
    server_hostname=os.getenv("DATABRICKS_HOST"),
    http_path=f"/sql/1.0/warehouses/{os.getenv('SQL_WAREHOUSE_ID')}",
    access_token=os.getenv("DATABRICKS_TOKEN")
)

cursor = connection.cursor()
for query in queries:
    print(f"\nExecuting: {query}")
    cursor.execute(query)
    result = cursor.fetchall()
    print(f"Result: {result[:5] if len(result) > 5 else result}")

cursor.close()
connection.close()
```

## 8. Performance Considerations

### Backend Optimizations Needed
1. **Create materialized views** for real-time queries
2. **Add indexes** on timestamp and sensor_id columns
3. **Implement caching layer** (Redis) between Databricks and frontend
4. **Use Delta Lake's change data feed** for real-time updates

### Frontend Optimizations
1. **Batch API calls** when possible
2. **Implement client-side caching** with 15-second TTL
3. **Use WebSocket connection** for real-time updates (future enhancement)
4. **Paginate large result sets**

## 9. Monitoring & Debugging

### Key Metrics to Track
- Query latency from Databricks
- Data freshness (timestamp lag)
- API error rates
- Frontend render performance with real data volumes

### Debug Endpoints to Implement
```javascript
// /api/debug/connection
// Returns: { databricks: 'connected' | 'error', latency: ms }

// /api/debug/data-freshness
// Returns: { lastUpdate: timestamp, lag: seconds }

// /api/debug/table-stats
// Returns: { bronze: count, silver: count, gold: count }
```

## 10. Demo Scenario Scripts

### Inject Demo Data
```python
# scripts/inject-demo-anomalies.py
# Injects anomalies for demo purposes
UPDATE sensor_data_silver
SET anomaly_detected = true,
    anomaly_score = 0.85
WHERE sensor_id IN ('WT-042', 'WT-078', 'WT-123')
AND timestamp > NOW() - INTERVAL 5 MINUTES
```

### Clear Demo Data
```python
# scripts/reset-demo-data.py
# Resets data to clean state after demo
UPDATE sensor_data_silver
SET anomaly_detected = false,
    anomaly_score = 0.0
WHERE anomaly_score > 0.7
```

---

## Quick Start for Frontend Developer

1. **Clone the repository**
2. **Copy `.env.example` to `.env` and fill in Databricks credentials**
3. **Run `scripts/test-frontend-queries.py` to verify connectivity**
4. **Start with mock data mode (`VITE_MOCK_DATA_ENABLED=true`)**
5. **Gradually enable real data endpoints one by one**
6. **Use `scripts/run-databricks-sql.py` to test your SQL queries**

## Support Contacts

- Backend Pipeline: Check `README.md` and `spot/instance-files/` for edge node configuration
- Databricks Setup: Check `MASTER_SETUP_AND_DEMO.md`
- Schema Questions: See `wind-turbine-schema.json`
- Deployment: Check deployment scripts in `scripts/` directory

---

This document provides the complete context needed to build the frontend dashboard that accurately reflects the data flowing through your Databricks pipeline.