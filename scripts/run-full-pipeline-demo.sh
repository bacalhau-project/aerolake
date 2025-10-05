#!/bin/bash

# Full Pipeline Demo - Runs edge processing demo
# Usage: ./run-full-pipeline-demo.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION=${AWS_REGION:-us-west-2}
STAGE_DURATION=60  # Run each stage for 60 seconds

# Function to print colored headers
print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${GREEN}  $1${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}\n"
}

# Function to print status
print_status() {
    echo -e "${YELLOW}➜${NC} $1"
}

# Function to print info
print_info() {
    echo -e "${CYAN}ℹ${NC}  $1"
}

# Function to check bucket with counts (SKIPPED - Expanso environment)
check_bucket_status() {
    local bucket=$1

    print_status "Pipeline stage: $bucket"
    echo "  ${CYAN}ℹ${NC} S3 bucket checks skipped in Expanso environment"
    echo "  ${CYAN}ℹ${NC} Data flow happens within Expanso cluster"
}

# Function to show countdown timer
countdown() {
    local seconds=$1
    local message=$2
    
    echo -e "${GREEN}$message${NC}"
    for i in $(seq $seconds -1 1); do
        echo -ne "${YELLOW}⏳ ${i} seconds remaining...\r${NC}"
        sleep 1
    done
    echo -e "${GREEN}✓ Stage complete!${NC}"
    echo
}

# Function to validate environment
validate_environment() {
    print_header "ENVIRONMENT VALIDATION"
    
    local errors=0
    
    # Check for required commands
    for cmd in docker expanso aws; do
        if ! command -v $cmd &> /dev/null; then
            print_error "Required command '$cmd' not found"
            errors=$((errors + 1))
        fi
    done
    
    # Check for required files
    if [ ! -f ".env" ]; then
        print_error "Environment file (.env) not found"
        errors=$((errors + 1))
    fi
    
    if [ $errors -gt 0 ]; then
        print_error "Environment validation failed with $errors errors"
        exit 1
    fi
    
    print_info "Environment validation passed"
}

# Initial status check
print_header "INITIAL STATUS CHECK"
print_info "Skipping S3 bucket checks - running in Expanso environment"
print_info "Data processing happens within Expanso cluster nodes"

# Validate environment
validate_environment

# STAGE 1: RAW MODE
print_header "STAGE 1: RAW DATA PROCESSING"
print_info "Running edge nodes in RAW mode for $STAGE_DURATION seconds..."
print_info "All sensor data will be processed as-is"

# Submit RAW processing job
expanso job run jobs/edge-processing-job.yaml \
    --template-vars pipeline_type=raw \
    --force

countdown $STAGE_DURATION "Processing RAW data at edge nodes..."

# STAGE 2: VALIDATED MODE
print_header "STAGE 2: VALIDATED DATA PROCESSING"
print_info "Running edge nodes in VALIDATED mode for $STAGE_DURATION seconds..."
print_info "Only physics-valid data will be uploaded"

# Submit VALIDATED processing job
expanso job run jobs/edge-processing-job.yaml \
    --template-vars pipeline_type=validated \
    --force

countdown $STAGE_DURATION "Processing VALIDATED data at edge nodes..."

# STAGE 3: ANOMALY DETECTION MODE
print_header "STAGE 3: ANOMALY DETECTION"
print_info "Running edge nodes in ANOMALY mode for $STAGE_DURATION seconds..."
print_info "Only anomalous data will be flagged and uploaded"

# Submit ANOMALY processing job
expanso job run jobs/edge-processing-job.yaml \
    --template-vars pipeline_type=anomaly \
    --force

countdown $STAGE_DURATION "Processing ANOMALY data at edge nodes..."

# STAGE 4: SCHEMATIZED MODE
print_header "STAGE 4: SCHEMATIZED DATA PROCESSING"
print_info "Running edge nodes in SCHEMATIZED mode for $STAGE_DURATION seconds..."
print_info "Data will be validated against JSON schema before upload"

# Submit SCHEMATIZED processing job
expanso job run jobs/edge-processing-job.yaml \
    --template-vars pipeline_type=schematized \
    --force

countdown $STAGE_DURATION "Processing SCHEMATIZED data at edge nodes..."

# STAGE 5: AGGREGATED MODE
print_header "STAGE 5: AGGREGATED DATA PROCESSING"
print_info "Running edge nodes in AGGREGATED mode for $STAGE_DURATION seconds..."
print_info "Data will be aggregated before upload"

# Submit AGGREGATED processing job
expanso job run jobs/edge-processing-job.yaml \
    --template-vars pipeline_type=aggregated \
    --force

countdown $STAGE_DURATION "Processing AGGREGATED data at edge nodes..."

# FINAL SUMMARY
print_header "DEMO COMPLETE"
print_info "All pipeline stages have been demonstrated"
print_info "Data has flowed through all processing modes"
echo ""
echo "Pipeline Summary:"
echo "  • RAW:         All sensor data processed"
echo "  • VALIDATED:   Physics-valid data uploaded"
echo "  • ANOMALY:     Anomalous readings flagged"
echo "  • SCHEMATIZED: Schema-validated data uploaded"
echo "  • AGGREGATED:  Summarized data uploaded"
echo ""
print_info "Next steps:"
print_info "  1. Check Databricks for processed data"
print_info "  2. Review AutoLoader notebooks"
print_info "  3. Monitor edge node status"