#!/bin/bash

# Full Pipeline Demo - Runs each stage for 1 minute to show data flow
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

# Function to check bucket with counts
check_bucket_status() {
    local bucket=$1
    local bucket_name="expanso-${bucket}-data-${AWS_REGION}"
    
    print_status "Checking $bucket bucket..."
    
    # Get file count and size
    local stats=$(aws s3 ls "s3://${bucket_name}/" --recursive --summarize \
        --no-paginator 2>/dev/null | tail -2)
    
    if [ -n "$stats" ]; then
        echo "  ${GREEN}✓${NC} $(echo "$stats" | grep "Total Objects" | awk '{print $3}') files"
        echo "  ${GREEN}✓${NC} $(echo "$stats" | grep "Total Size" | awk '{print $3, $4}')"
    else
        echo "  ${RED}✗${NC} Empty or inaccessible"
    fi
}

# Function to show countdown timer
countdown() {
    local seconds=$1
    local message=$2
    
    while [ $seconds -gt 0 ]; do
        printf "\r${CYAN}⏱${NC}  $message: ${GREEN}${seconds}s${NC} remaining... "
        sleep 1
        ((seconds--))
    done
    printf "\r${GREEN}✓${NC} $message: Complete!                    \n"
}

# Main demo execution
main() {
    print_header "FULL PIPELINE DEMO - 1 MINUTE PER STAGE"
    
    print_info "This demo will run each pipeline stage for 1 minute"
    print_info "Sensors are already running on all compute nodes"
    print_info "We'll switch modes and observe data flow\n"
    
    # Initial status check
    print_header "INITIAL STATUS CHECK"
    for bucket in ingestion validated anomalies enriched aggregated; do
        check_bucket_status "$bucket"
    done
    
    # STAGE 1: RAW MODE
    print_header "STAGE 1: RAW MODE"
    print_info "All sensor data flows directly to ingestion bucket"
    print_info "No validation or filtering applied\n"
    
    print_status "Switching to RAW mode..."
    bacalhau job run jobs/pipeline-manager-switch.yaml \
        --template-vars pipeline_type=raw --force --wait
    
    countdown $STAGE_DURATION "Processing in RAW mode"
    
    check_bucket_status "ingestion"
    
    # STAGE 2: SCHEMATIZED MODE (for validation)
    print_header "STAGE 2: SCHEMATIZED MODE"
    print_info "Data is validated against wind turbine schema"
    print_info "Valid records → validated bucket"
    print_info "Invalid records → anomalies bucket\n"
    
    print_status "Switching to SCHEMATIZED mode..."
    bacalhau job run jobs/pipeline-manager-switch.yaml \
        --template-vars pipeline_type=schematized --force --wait
    
    countdown $STAGE_DURATION "Processing with validation"
    
    check_bucket_status "validated"
    check_bucket_status "anomalies"
    
    # STAGE 3: FILTERED MODE
    print_header "STAGE 3: FILTERED MODE"
    print_info "Data is filtered and enriched"
    print_info "Processed data → enriched bucket\n"
    
    print_status "Switching to FILTERED mode..."
    bacalhau job run jobs/pipeline-manager-switch.yaml \
        --template-vars pipeline_type=filtered --force --wait
    
    countdown $STAGE_DURATION "Processing with filtering"
    
    check_bucket_status "enriched"
    
    # STAGE 4: AGGREGATED MODE
    print_header "STAGE 4: AGGREGATED MODE"
    print_info "Data is aggregated for analytics"
    print_info "Aggregated metrics → aggregated bucket\n"
    
    print_status "Switching to AGGREGATED mode..."
    bacalhau job run jobs/pipeline-manager-switch.yaml \
        --template-vars pipeline_type=aggregated --force --wait
    
    countdown $STAGE_DURATION "Processing with aggregation"
    
    check_bucket_status "aggregated"
    
    # STAGE 5: ANOMALY MODE
    print_header "STAGE 5: ANOMALY MODE"
    print_info "Focus on anomaly detection"
    print_info "Anomalous data → anomalies bucket\n"
    
    print_status "Switching to ANOMALY mode..."
    bacalhau job run jobs/pipeline-manager-switch.yaml \
        --template-vars pipeline_type=anomaly --force --wait
    
    countdown $STAGE_DURATION "Detecting anomalies"
    
    check_bucket_status "anomalies"
    
    # FINAL SUMMARY
    print_header "FINAL SUMMARY"
    
    print_status "Checking all buckets after full pipeline run..."
    echo ""
    
    for bucket in ingestion validated anomalies enriched aggregated; do
        check_bucket_status "$bucket"
        echo ""
    done
    
    # Get current pipeline state
    print_status "Current pipeline configuration:"
    bacalhau job run jobs/debug-pipeline-state.yaml --force --wait 2>&1 | \
        grep -A 10 "Standard Output" | tail -n +2 || true
    
    print_header "DEMO COMPLETE"
    
    print_info "Total demo duration: $(( STAGE_DURATION * 5 )) seconds"
    print_info "Each stage processed data for $STAGE_DURATION seconds"
    
    echo -e "\n${GREEN}✓${NC} Pipeline demo completed successfully!"
    echo -e "${CYAN}ℹ${NC}  Run 'uv run scripts/query-data-summary.py' for detailed statistics"
    echo -e "${CYAN}ℹ${NC}  Sensors continue running on all compute nodes"
}

# Check prerequisites
check_prerequisites() {
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}Error: AWS CLI is not installed${NC}"
        exit 1
    fi
    
    if ! command -v bacalhau &> /dev/null; then
        echo -e "${RED}Error: Bacalhau CLI is not installed${NC}"
        exit 1
    fi
    
    if [ ! -f "jobs/pipeline-manager-switch.yaml" ]; then
        echo -e "${RED}Error: Not in the correct directory. Run from project root.${NC}"
        exit 1
    fi
}

# Run the demo
check_prerequisites
main "$@"