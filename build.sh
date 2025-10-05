#!/bin/bash
# Build script for Expanso Edge pipeline components

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[BUILD]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Default values
COMPONENT=""
PUSH=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --component)
            COMPONENT="$2"
            shift 2
            ;;
        --push)
            PUSH="true"
            shift
            ;;
        --help)
            echo "Usage: $0 --component COMPONENT [OPTIONS]"
            echo ""
            echo "Components:"
            echo "  sensor             Build sensor-log-generator image"
            echo "  all                Build all components"
            echo ""
            echo "Options:"
            echo "  --push             Push images to registry after build"
            echo ""
            echo "Examples:"
            echo "  $0 --component sensor"
            echo "  $0 --component sensor --push"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$COMPONENT" ]; then
    print_error "Component is required. Use --component to specify what to build."
    print_error "See --help for available components."
    exit 1
fi

# Function to build sensor image
build_sensor() {
    print_status "Building sensor-log-generator image..."
    
    # Build the sensor image
    docker build -t ghcr.io/expanso-io/sensor-log-generator:latest \
        -f spot/instance-files/opt/sensor/Dockerfile \
        spot/instance-files/opt/sensor/
    
    print_status "Sensor image built successfully!"
    
    # Tag with timestamp
    local timestamp=$(date +%Y%m%d-%H%M%S)
    docker tag ghcr.io/expanso-io/sensor-log-generator:latest \
        ghcr.io/expanso-io/sensor-log-generator:$timestamp
    
    print_info "Also tagged as: ghcr.io/expanso-io/sensor-log-generator:$timestamp"
    
    # Save tag for reference
    echo "sensor-log-generator:$timestamp" > .latest-image-tag
    
    # Push if requested
    if [ "$PUSH" == "true" ]; then
        print_status "Pushing sensor image to registry..."
        docker push ghcr.io/expanso-io/sensor-log-generator:latest
        docker push ghcr.io/expanso-io/sensor-log-generator:$timestamp
        print_status "Sensor image pushed successfully!"
    fi
}

# Function to build all components
build_all() {
    print_status "Building all components..."
    build_sensor
    print_status "All components built successfully!"
}

# Main execution
case $COMPONENT in
    sensor)
        build_sensor
        ;;
    all)
        build_all
        ;;
    *)
        print_error "Unknown component: $COMPONENT"
        print_error "Valid components: sensor, all"
        exit 1
        ;;
esac