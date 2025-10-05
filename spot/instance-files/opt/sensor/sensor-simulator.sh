#!/bin/bash
# Simple sensor simulator script

CONFIG_FILE=${CONFIG_FILE:-/config/sensor-config.yaml}
IDENTITY_FILE=${IDENTITY_FILE:-/config/node_identity.json}
DATA_DIR=${DATA_DIR:-/app/data}
LOGS_DIR=${LOGS_DIR:-/app/logs}

# Create directories if they don't exist
mkdir -p "$DATA_DIR" "$LOGS_DIR"

# Log startup
echo "$(date): Sensor simulator started" >> "$LOGS_DIR/sensor.log"

# If identity file doesn't exist, create a simple one
if [ ! -f "$IDENTITY_FILE" ]; then
    echo "Creating node identity file..."
    cat > "$IDENTITY_FILE" <<EOF
{
  "node_id": "$(hostname)",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
fi

# Main loop - generate some sample data
while true; do
    # Generate a simple JSON log entry
    TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    VALUE=$((RANDOM % 100))
    
    echo "{\"timestamp\":\"$TIMESTAMP\",\"sensor_id\":\"$(hostname)\",\"value\":$VALUE}" >> "$DATA_DIR/sensor-data.log"
    echo "$(date): Generated sensor data - Value: $VALUE" >> "$LOGS_DIR/sensor.log"
    
    # Wait before generating next data point
    sleep 10
done