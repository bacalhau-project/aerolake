#!/bin/bash

# Pipeline Demo Script - Exercise all stages of the data pipeline
# Usage: ./run-pipeline-demo.sh [stage]
# Stages: raw, filtered, aggregated, anomaly, all

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION=${AWS_REGION:-us-west-2}

# Function to print colored headers
print_header() {
    echo -e "\n${BLUE}===========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${BLUE}===========================================${NC}\n"
}

# Function to print status
print_status() {
    echo -e "${YELLOW}➜${NC} $1"
}

# Function to wait for user confirmation
wait_for_enter() {
    echo -e "\n${GREEN}Done${NC}"
}

# Function to run RAW pipeline stage
run_raw_stage() {
    print_header "STAGE 1: RAW MODE - Collect Everything"

    print_status "Setting pipeline to RAW mode (no filtering)..."
    bacalhau job run jobs/pipeline-manager-switch.yaml \
        --template-vars pipeline_type=raw --force --wait

    print_status "Pipeline switched to RAW mode"

    wait_for_enter
}

# Function to run FILTERED pipeline stage
run_filtered_stage() {
    print_header "STAGE 2: FILTERED MODE - Split Valid/Invalid"

    print_status "Switching to FILTERED mode (validation enabled)..."
    bacalhau job run jobs/pipeline-manager-switch.yaml \
        --template-vars pipeline_type=filtered --force --wait

    print_status "Pipeline switched to FILTERED mode"

    wait_for_enter
}

# Function to run AGGREGATED pipeline stage
run_aggregated_stage() {
    print_header "STAGE 3: AGGREGATED MODE - Enable Aggregations"

    print_status "Switching to AGGREGATED mode..."
    bacalhau job run jobs/pipeline-manager-switch.yaml \
        --template-vars pipeline_type=aggregated --force --wait

    print_status "Pipeline switched to AGGREGATED mode"

    wait_for_enter
}

# Function to run SCHEMATIZED pipeline stage
run_schematized_stage() {
    print_header "SCHEMATIZED MODE - Validate and Split Data"

    print_status "Switching to SCHEMATIZED mode (enables validation)..."
    bacalhau job run jobs/pipeline-manager-switch.yaml \
        --template-vars pipeline_type=schematized --force --wait

    print_status "Pipeline switched to SCHEMATIZED mode - data will be validated and split"
    print_status "Valid data → validated bucket"
    print_status "Invalid data → anomalies bucket"

    wait_for_enter
}

# Function to run ANOMALY pipeline stage
run_anomaly_stage() {
    print_header "STAGE 4: ANOMALY MODE - Focus on Anomalies"

    print_status "Switching to ANOMALY mode (prioritize anomaly detection)..."
    bacalhau job run jobs/pipeline-manager-switch.yaml \
        --template-vars pipeline_type=anomaly --force --wait

    print_status "Pipeline switched to ANOMALY mode"

    print_status "Checking current pipeline state..."
    bacalhau job run jobs/debug-pipeline-state.yaml --force --wait

    wait_for_enter
}

# Function to clean up resources
cleanup() {
    print_header "CLEANUP"

    print_status "Note: Sensors continue running on all compute nodes"
    print_status "Cleanup complete"
}

# Main execution
main() {
    local stage=${1:-help}

    # Check if we should run in auto mode (no pauses)
    if [ "$2" == "--auto" ]; then
        AUTO_MODE=true
        print_status "Running in automatic mode (no pauses)"
    fi

    case $stage in
        raw)
            run_raw_stage
            ;;
        filtered)
            run_filtered_stage
            ;;
        schematized)
            run_schematized_stage
            ;;
        aggregated)
            run_aggregated_stage
            ;;
        anomaly)
            run_anomaly_stage
            ;;
        all)
            print_header "RUNNING ALL PIPELINE STAGES"
            run_raw_stage
            run_filtered_stage
            run_schematized_stage
            run_aggregated_stage
            run_anomaly_stage
            ;;
        verify)
            verify_all_stages
            ;;
        cleanup)
            cleanup
            ;;
        *)
            echo "Usage: $0 [stage] [--auto]"
            echo "Stages:"
            echo "  raw         - Run RAW mode stage only"
            echo "  filtered    - Run FILTERED mode stage only"
            echo "  schematized - Run SCHEMATIZED mode (validates & splits data)"
            echo "  aggregated  - Run AGGREGATED mode stage only"
            echo "  anomaly     - Run ANOMALY mode stage only"
            echo "  all         - Run all stages in sequence (default)"
            echo "  verify      - Verify all buckets have data"
            echo "  cleanup     - Stop sensors and clean up"
            echo ""
            echo "Options:"
            echo "  --auto     - Run without pausing between stages"
            exit 1
            ;;
    esac

    print_header "DEMO COMPLETE"
    echo -e "${GREEN}✓ Pipeline demo finished successfully${NC}"
}

# Trap to ensure cleanup on exit (only for 'all' or 'cleanup' commands)
if [[ "$1" == "all" || "$1" == "cleanup" ]]; then
    trap cleanup EXIT
fi

# Run main function
main "$@"
