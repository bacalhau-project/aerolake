#!/bin/bash
# Comprehensive test script for Expanso Edge

set -e  # Exit on error

echo "=== Expanso Edge Test Suite ==="
echo

# Load environment variables
source .env

# 1. Environment Check
echo "1. Checking environment variables..."
echo "   AWS_REGION: ${AWS_REGION}"
echo "   S3_BUCKET_PREFIX: ${S3_BUCKET_PREFIX}"
echo "   DATABRICKS_HOST: ${DATABRICKS_HOST}"
echo "   ✓ Environment variables loaded"
echo

# 2. AWS S3 Check (using on-disk credentials)
echo "2. Testing AWS S3 connectivity..."
if [ -f "credentials/expanso-s3-env.sh" ]; then
    source credentials/expanso-s3-env.sh
    echo "   ✓ Loaded AWS credentials from credentials/expanso-s3-env.sh"
else
    echo "   ⚠  No local credentials file found - using environment variables"
fi

# Test S3 access
if aws s3 ls "s3://${S3_BUCKET_PREFIX}-raw-data-${AWS_REGION}" >/dev/null 2>&1; then
    echo "   ✓ S3 access successful"
else
    echo "   ✗ S3 access failed - check credentials and bucket permissions"
    exit 1
fi
echo

# 3. Docker Check
echo "3. Testing Docker connectivity..."
if docker version >/dev/null 2>&1; then
    echo "   ✓ Docker daemon accessible"
else
    echo "   ✗ Docker daemon not accessible"
    exit 1
fi
echo

# 4. Expanso Check
echo "4. Testing Expanso CLI..."
if command -v expanso >/dev/null 2>&1; then
    echo "   ✓ Expanso CLI installed"
    expanso version
else
    echo "   ✗ Expanso CLI not installed"
    exit 1
fi
echo

# 5. Sensor Data Check
echo "5. Checking sensor data..."
if [ -f "sample-sensor/data/sensor_data.db" ]; then
    echo "   ✓ Sensor database found"
    RECORD_COUNT=$(sqlite3 sample-sensor/data/sensor_data.db "SELECT COUNT(*) FROM sensor_readings;" 2>/dev/null || echo "0")
    echo "   ✓ Database contains $RECORD_COUNT records"
else
    echo "   ⚠  Sensor database not found - run sensor simulator first"
fi
echo

# 6. Job Specification Check
echo "6. Checking job specifications..."
if [ -f "jobs/edge-processing-job.yaml" ]; then
    echo "   ✓ Edge processing job specification found"
else
    echo "   ✗ Edge processing job specification not found"
    exit 1
fi
echo

# 7. Instance Files Check
echo "7. Checking instance files..."
if [ -d "spot/instance-files" ]; then
    echo "   ✓ Instance files directory found"
    if [ -f "spot/instance-files/setup.sh" ]; then
        echo "   ✓ Node setup script found"
    else
        echo "   ⚠  Node setup script not found"
    fi
else
    echo "   ✗ Instance files directory not found"
    exit 1
fi
echo

echo "=== All tests completed successfully! ==="
echo
echo "Next steps:"
echo "  1. Deploy edge nodes using spot/instance-files"
echo "  2. Start sensor data generation: ./run.sh --component sensor"
echo "  3. Submit edge processing jobs: expanso job run jobs/edge-processing-job.yaml"