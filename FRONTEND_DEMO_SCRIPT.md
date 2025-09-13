# Frontend Demo Script - Environmental Sensor Data Pipeline

This comprehensive script outlines exactly what the frontend needs to show for a complete demo of the backend environmental sensor data pipeline functionality. This document serves as the requirements specification for frontend developers to build a demo-ready interface.

## Overview

The backend system is an **Environmental Sensor Data Pipeline** that processes sensor data (temperature, humidity, pressure, vibration, voltage) through multiple stages:

1. **Raw Data Collection** → 2. **Validation** → 3. **Anomaly Detection** → 4. **Schema Transformation** → 5. **Aggregation**

The frontend must demonstrate real-time monitoring of this multi-stage pipeline with visual representations of data flow, anomaly detection, and processing metrics.

## Core Frontend Requirements

### 1. Navigation & Layout

**Main Navigation Bar:**
- Logo/Brand: "Environmental Sensor Pipeline"
- Active Pipeline Status Indicator: `● LIVE` with pulsing animation
- Real-time Record Counter: "Records: 1.2M/s" (updating live)
- Navigation Tabs:
  - **Sensors Overview** (sensor map and status)
  - **Raw Data** (ingestion pipeline)
  - **Validated Data** (validation results)
  - **Anomalies** (anomaly detection)
  - **Schematized** (structured data)
  - **Aggregated** (analytics-ready data)

**Page Structure:**
```
[Header with Navigation]
[Real-time Status Bar]
[Main Content Area]
[Live Data Feed Footer]
```

### 2. Sensors Overview Page (`/sensors`)

**Interactive World Map:**
- Dark theme map with sensor locations
- 50-100 sensor markers with pulsing animations
- Color-coded status indicators:
  - 🟢 Green: Normal operation
  - 🟡 Yellow: Warning conditions
  - 🔴 Red: Critical anomalies
  - 🟣 Purple: Sensor offline
- Click/hover popups showing:
  ```
  Sensor CHI_123456
  Location: Chicago, IL
  Temp: 62.5°C ↑
  Status: ● Active
  Last: 2 seconds ago
  ```

**Sensor Grid Cards:**
- Responsive grid layout
- Each card shows:
  - Sensor ID (e.g., "CHI_123456")
  - Location name
  - Live mini-sparkline (last 20 readings)
  - Current temperature with trend arrow
  - Status dot indicator
  - Glow effect on data updates

**Real-time Metrics Panel:**
- Total Active Sensors: 147
- Data Points/Second: 1,247
- Anomaly Rate: 3.2%
- System Uptime: 99.8%

### 3. Raw Data Pipeline Page (`/raw`)

**Pipeline Flow Visualization:**
```
[Sensors] ══════> [Ingestion] ══════> [S3 Storage] ══════> [Processing Queue]
   📡                 ⚙️                 💾                     ⏳
```
- Animated data packets flowing along pipes
- Pipe thickness represents throughput volume
- Glow intensity shows processing activity

**Live Data Stream Terminal:**
- Matrix-style scrolling JSON data
- Syntax-highlighted JSON records
- Auto-scrolling with momentum
- Sample display:
```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "sensor_id": "CHI_123456",
  "temperature": 62.5,
  "humidity": 35.2,
  "pressure": 12.3,
  "vibration": 0.0,
  "voltage": 12.1,
  "location": "Chicago"
}
```

**Processing Statistics:**
- Records Ingested/Hour: 4.3M
- Average Processing Time: 125ms
- Queue Depth: 1,247 records
- Storage Usage: 847GB

### 4. Validated Data Page (`/validated`)

**Validation Pipeline:**
```
[Raw Data] ──> [Physics Rules] ──> [Range Checks] ──> [Validated Storage]
                    🔍                 📊                  ✅
```

**Before/After Data Comparison:**
- Split-screen layout
- Left: Raw sensor reading
- Right: Validated & enriched data
- Diff highlighting:
  - 🟢 Green: Added validation fields
  - 🔵 Blue: Modified values
  - 🟡 Yellow: Type conversions

**Validation Rules Dashboard:**
- Temperature: -20°C to 60°C ✅ Pass Rate: 98.7%
- Humidity: 0% to 100% ✅ Pass Rate: 99.2%  
- Pressure: 10.5-14.5 bar ✅ Pass Rate: 97.8%
- Vibration: < 0.5 units ✅ Pass Rate: 94.3%
- Voltage: 11.6-12.4V ✅ Pass Rate: 96.5%

**Live Validation Counter:**
- Valid Records: 1,234,567
- Failed Validation: 45,123 (3.5%)
- Processing Rate: 847 records/sec

### 5. Anomaly Detection Page (`/anomalies`)

**Anomaly Processing Flow:**
```
                    ┌──> [Normal Data] ──> [Validated Storage]
[Sensor Data] ──────┤
                    └──> [Anomalies] ──> [Alert System] ──> [Investigation Queue]
```

**Real-time Anomaly Feed:**
- Sliding cards showing detected anomalies
- Each card displays:
  - Timestamp
  - Sensor ID & Location
  - Anomaly Type (spike, trend, pattern, missing_data, noise)
  - Severity Score (0.0 - 1.0)
  - Affected Metrics
  - Auto-generated Alert Status

**Anomaly Types Breakdown:**
- 🔥 **Temperature Spikes**: 23 alerts (15 critical)
- 📈 **Trend Anomalies**: 8 alerts (2 critical)  
- 🌊 **Vibration Patterns**: 12 alerts (7 critical)
- ⚡ **Voltage Issues**: 5 alerts (1 critical)
- 📊 **Data Quality**: 3 alerts (0 critical)

**Anomaly Investigation Panel:**
- Time-series charts showing anomaly context
- Correlation with nearby sensors
- Suggested maintenance actions
- Historical pattern analysis

### 6. Schematized Data Page (`/schematized`)

**Schema Transformation Pipeline:**
```
[Validated] ──> [Schema Enforcement] ──> [Type Conversion] ──> [Unity Catalog]
                      📋                      🔄                    🗄️
```

**Schema Evolution Tracking:**
- Current Schema Version: v2.3.1
- Fields Added Today: 3
- Backward Compatibility: ✅ Maintained
- Migration Status: Complete

**Data Structure Visualization:**
- Interactive schema tree
- Field types and constraints
- Transformation rules applied
- Sample transformed records

**Schema Compliance Metrics:**
- Records Processed: 2.1M
- Schema Violations: 156 (0.007%)
- Transformation Success Rate: 99.99%
- Processing Latency: 45ms avg

### 7. Aggregated Data Page (`/aggregated`)

**Aggregation Pipeline:**
```
[Schematized] ──> [Time Windows] ──> [Statistical Functions] ──> [Analytics Store]
                      ⏰                      📊                      📈
```

**Time Window Controls:**
- 1-minute windows ✓ (selected)
- 5-minute windows
- 15-minute windows  
- 1-hour windows
- Custom range picker

**Aggregated Metrics Display:**
- **Temperature**: Avg 23.4°C, Min 18.2°C, Max 28.7°C
- **Humidity**: Avg 45.2%, Min 12%, Max 78%
- **Pressure**: Avg 12.1 bar, Min 10.8 bar, Max 13.4 bar
- **Vibration**: Avg 0.12 units, Max 0.89 units
- **Voltage**: Avg 12.0V, Min 11.7V, Max 12.3V

**Analytics-Ready Data Preview:**
```json
{
  "window_start": "2024-01-15T10:30:00Z",
  "window_end": "2024-01-15T10:31:00Z", 
  "sensor_count": 147,
  "total_readings": 8820,
  "avg_temperature": 23.4,
  "anomaly_count": 12,
  "data_quality_score": 0.987
}
```

## Real-time Data Requirements

### WebSocket Connection
**Endpoint:** `ws://localhost:8000/ws`
**Updates Required:**
- Pipeline status changes
- Live sensor readings (throttled to 1-second updates)
- Anomaly alerts (immediate)
- Processing metrics (5-second intervals)
- System health status

### Server-Sent Events (SSE)
**Endpoint:** `GET /api/events/stream`
**Data Stream:**
```json
{
  "event": "metrics_update",
  "data": {
    "timestamp": "2024-01-15T10:30:45Z",
    "upload_rate": 12.5,
    "quality_score": 0.89,
    "active_sensors": 145,
    "anomaly_count": 23
  }
}
```

## API Endpoints for Frontend Integration

### Core Status APIs
- `GET /api/pipeline/status` - Current pipeline configuration
- `GET /api/pipeline/history` - Pipeline execution history
- `GET /api/uploads/metrics` - S3 upload statistics
- `GET /api/uploads/recent` - Recent upload details

### Data Quality APIs  
- `POST /api/quality/validate` - Validate data file upload
- `GET /api/quality/metrics` - Quality metrics over time

### Sensor Data APIs
- `GET /api/turbines/metrics` - Real-time sensor metrics
- `GET /api/turbines/metrics?farm_id=CHI&limit=100` - Filtered data

### Alert Management APIs
- `GET /api/alerts/config` - Alert configuration
- `PUT /api/alerts/config/{alert_name}` - Update alert settings

### Health Check
- `GET /health` - API health status

## Data Models for Frontend

### Sensor Reading Data Structure
```typescript
interface SensorReading {
  timestamp: string;
  sensor_id: string;           // Format: "CHI_123456"
  temperature: number;         // -20 to 60°C
  humidity: number;           // 0-100%
  pressure: number;           // 10.5-14.5 bar
  vibration: number;          // 0+ units
  voltage: number;            // 11.6-12.4V
  status_code: 0 | 1;        // 0=normal, 1=anomaly
  anomaly_flag: boolean;
  anomaly_type?: "spike" | "trend" | "pattern" | "missing_data" | "noise";
  location: string;
  latitude: number;
  longitude: number;
}
```

### Pipeline Status
```typescript
interface PipelineStatus {
  pipeline_type: "raw" | "ingestion" | "validated" | "anomalies" | "schematized" | "aggregated";
  updated_at: string;
  updated_by: string;
  is_active: boolean;
  recent_uploads: number;
  error_rate: number;
  average_quality_score: number;
}
```

### Anomaly Alert
```typescript
interface AnomalyAlert {
  timestamp: string;
  sensor_id: string;
  anomaly_type: string;
  severity_score: number;     // 0.0 - 1.0
  affected_metrics: string[];
  location: string;
  investigation_status: "new" | "investigating" | "resolved";
}
```

## Visual Design Requirements

### Color Scheme
```css
:root {
  --primary-blue: #1E40AF;
  --success-green: #10B981;
  --warning-amber: #F59E0B;
  --danger-red: #EF4444;
  --anomaly-purple: #8B5CF6;
  --background-dark: #0F172A;
  --surface-dark: #1E293B;
  --text-light: #F1F5F9;
  --accent-cyan: #06B6D4;
}
```

### Animation Requirements
- **Pulse Effects**: 2s cycle for sensor status indicators
- **Data Flow**: Animated particles moving along pipeline pipes
- **Number Counters**: Spring physics animation for metric updates
- **Page Transitions**: 300ms slide + fade between views
- **Loading States**: Shimmer effects for data loading
- **Hover Effects**: 150ms scale + glow for interactive elements

## Demo Flow Script

### 5-Minute Demo Walkthrough

**Minute 1: Overview & Setup**
1. Show navigation header with live status
2. Display sensor overview map with active sensors
3. Point out real-time counters and metrics

**Minute 2: Data Ingestion**  
4. Navigate to Raw Data page
5. Show live data stream terminal
6. Highlight processing statistics and throughput

**Minute 3: Validation & Quality**
7. Go to Validated Data page
8. Show before/after comparison
9. Demonstrate validation rules dashboard

**Minute 4: Anomaly Detection**
10. Navigate to Anomalies page
11. Show real-time anomaly feed
12. Explain different anomaly types and alerts

**Minute 5: Final Processing**
13. Show Schematized data transformation
14. End on Aggregated data analytics view
15. Summarize the complete pipeline flow

## Mock Data for Development

### Sample Sensor Locations (Global Distribution)
```javascript
const SENSOR_LOCATIONS = [
  { id: "CHI_123456", city: "Chicago", lat: 41.8781, lng: -87.6298, status: "active" },
  { id: "NYC_789012", city: "New York", lat: 40.7128, lng: -74.0060, status: "active" },
  { id: "LAX_345678", city: "Los Angeles", lat: 34.0522, lng: -118.2437, status: "warning" },
  { id: "LON_901234", city: "London", lat: 51.5074, lng: -0.1278, status: "active" },
  { id: "TOK_567890", city: "Tokyo", lat: 35.6762, lng: 139.6503, status: "critical" },
  // ... 45 more sensors for a total of 50
];
```

### Sample Anomaly Types with Realistic Data
```javascript
const ANOMALY_EXAMPLES = [
  {
    type: "temperature_spike",
    description: "Temperature exceeded 45°C for 5+ minutes", 
    severity: 0.85,
    action: "Investigate cooling system"
  },
  {
    type: "vibration_pattern", 
    description: "Unusual vibration frequency detected",
    severity: 0.72,
    action: "Schedule mechanical inspection"
  },
  {
    type: "voltage_fluctuation",
    description: "Voltage drops below 11.6V repeatedly", 
    severity: 0.68,
    action: "Check power supply connection"
  }
];
```

## Performance Requirements

### Real-time Updates
- **WebSocket**: Maximum 1-second latency for critical alerts
- **Data Refresh**: Pipeline metrics update every 5 seconds
- **Animations**: Maintain 60fps for all visual effects
- **API Response**: < 200ms for status endpoints

### Scalability Targets  
- **Concurrent Users**: Support 10+ simultaneous demo viewers
- **Data Volume**: Display metrics for 1M+ records/hour processing
- **Historical Data**: Show trends over 24-hour periods
- **Memory Usage**: < 100MB frontend application size

## Error Handling & Fallbacks

### Graceful Degradation
- **API Unavailable**: Switch to mock data automatically
- **WebSocket Disconnected**: Show "Reconnecting..." status
- **Slow Loading**: Display skeleton screens
- **Invalid Data**: Show error state with retry option

### Demo-Safe Fallbacks
- Always have mock data ready for offline demos
- Never show error messages during presentations
- Automatic retry mechanisms for all API calls
- Fallback animations when real data unavailable

## Deployment & Configuration

### Environment Variables
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_UPDATE_INTERVAL=1000
VITE_MOCK_DATA_ENABLED=true
VITE_DEMO_MODE=true
```

### Production Readiness
- Static build deployment (no backend required for demo)
- CDN-ready asset optimization
- Mobile-responsive design (tablet minimum)
- Cross-browser compatibility (Chrome, Firefox, Safari, Edge)

---

## Summary

This frontend must showcase a complete **environmental sensor data pipeline** with:

1. **147 active sensors** across global locations
2. **Multi-stage data processing** (Raw → Validated → Anomalies → Schematized → Aggregated)
3. **Real-time anomaly detection** with alert management
4. **Physics-based validation** rules for sensor data
5. **Live data streaming** with WebSocket/SSE connections
6. **Interactive visualizations** and monitoring dashboards

The frontend should convey the sophistication of an enterprise-grade IoT data pipeline while maintaining a smooth, demo-ready user experience that never fails visibly.

**Key Message**: "Watch environmental sensor data flow through our intelligent pipeline in real-time, with automatic anomaly detection and enterprise-grade data quality assurance."