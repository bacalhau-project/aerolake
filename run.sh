#!/bin/bash
# Run script for Expanso Edge pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[RUN]${NC} $1"
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
MODE="local"
COMPONENT=""
ENV_FILE=".env"
DETACH=""
FOLLOW_LOGS=""
PULL_LATEST="true"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --component)
            COMPONENT="$2"
            shift 2
            ;;
        --env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --detach|-d)
            DETACH="-d"
            shift
            ;;
        --follow-logs|-f)
            FOLLOW_LOGS="true"
            shift
            ;;
        --no-pull)
            PULL_LATEST="false"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --mode MODE         Run mode: local, docker, expanso \
(default: local)"
            echo "  --component NAME    Component to run: sensor, edge, all"
            echo "  --env-file FILE     Environment file (default: .env)"
            echo "  --detach, -d        Run in detached mode (Docker only)"
            echo "  --follow-logs, -f   Follow logs after starting"
            echo "  --no-pull           Don't pull latest images (Docker mode)"
            echo "  --help              Show this help message"
            echo ""
            echo "Note: Docker mode always pulls latest images unless --no-pull is used"
            echo ""
            echo "Examples:"
            echo "  # Run sensor locally to generate data:"
            echo "  $0 --mode local --component sensor"
            echo ""
            echo "  # Run everything in Docker:"
            echo "  $0 --mode docker --component all -d"
            echo ""
            echo "  # Run on Expanso Edge:"
            echo "  $0 --mode expanso --component edge"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    print_error "Environment file not found: $ENV_FILE"
    print_info "Copy .env.example to .env and configure it"
    exit 1
fi

# Load environment variables
set -a
source "$ENV_FILE"
set +a

# Function to print Docker image version info
print_docker_version_info() {
    local image="$1"
    local component_name="$2"
    
    print_info "===== Docker Image Version Info for $component_name ====="
    
    # Get image digest and ID
    local image_id=$(docker images --no-trunc --quiet "$image" | head -1)
    local short_id=$(docker images --quiet "$image" | head -1)
    
    if [ -n "$image_id" ]; then
        print_info "Image ID: $short_id (full: ${image_id:7:19}...)"
        
        # Get image details
        local created=$(docker inspect "$image" --format='{{.Created}}' 2>/dev/null || echo "unknown")
        local digest=$(docker inspect "$image" --format='{{.RepoDigests}}' 2>/dev/null | grep -o 'sha256:[a-f0-9]*' | head -1 || echo "unknown")
        
        print_info "Created: $created"
        print_info "Digest: ${digest:-unknown}"
        
        # Try to get labels with version info
        local version=$(docker inspect "$image" --format='{{.Config.Labels.version}}' 2>/dev/null || echo "")
        local git_commit=$(docker inspect "$image" --format='{{.Config.Labels.git_commit}}' 2>/dev/null || echo "")
        local build_date=$(docker inspect "$image" --format='{{.Config.Labels.build_date}}' 2>/dev/null || echo "")
        
        [ -n "$version" ] && [ "$version" != "<no value>" ] && print_info "Version Label: $version"
        [ -n "$git_commit" ] && [ "$git_commit" != "<no value>" ] && print_info "Git Commit: $git_commit"
        [ -n "$build_date" ] && [ "$build_date" != "<no value>" ] && print_info "Build Date: $build_date"
    else
        print_warning "Image not found locally yet"
    fi
    
    # Check for local build tag file
    if [ -f ".latest-image-tag" ]; then
        local local_tag=$(cat .latest-image-tag)
        print_info "Local Build Tag: $local_tag"
    fi
    
    print_info "=========================================="
    echo ""
}

# Function to run sensor simulator
run_sensor() {
    print_status "Running sensor simulator..."
    
    # Always cleanup existing sensor container first
    if docker ps -a | grep -q sensor-log-generator; then
        print_warning "Cleaning up existing sensor container..."
        docker stop sensor-log-generator 2>/dev/null || true
        docker rm sensor-log-generator 2>/dev/null || true
    fi
    
    # Pull latest sensor image if enabled (for both local and docker modes)
    if [ "$PULL_LATEST" == "true" ]; then
        print_info "Pulling latest sensor-log-generator image..."
        docker pull ghcr.io/expanso-io/sensor-log-generator:latest || {
            print_warning "Could not pull sensor image from registry"
        }
        
        # Print version info after pulling
        print_docker_version_info "ghcr.io/expanso-io/sensor-log-generator:latest" "sensor-log-generator"
    fi
    
    print_info "This will run the sensor using the start-sensor.sh script"
    
    # Both local and docker modes use the same script (it runs Docker)
    ./scripts/start-sensor.sh
}

# Function to check dependencies
check_dependencies() {
    local deps_missing=false
    
    case $MODE in
        local)
            # Local mode doesn't require special dependencies for sensor
            ;;
        docker)
            if ! command -v docker &> /dev/null; then
                print_error "Docker is not installed"
                deps_missing=true
            fi
            ;;
        expanso)
            # Expanso mode - check for Docker (Edge runs in containers)
            if ! command -v docker &> /dev/null; then
                print_error "Docker is required for Expanso mode"
                deps_missing=true
            fi
            ;;
    esac
    
    if [ "$deps_missing" == "true" ]; then
        exit 1
    fi
}

# Main execution
check_dependencies

case $COMPONENT in
    sensor)
        run_sensor
        ;;
    edge)
        if [ "$MODE" == "expanso" ]; then
            print_status "Running on Expanso Edge..."
            print_info "Expanso Edge deployment handled by instance files"
        else
            print_error "Edge component only supported with --mode expanso"
            exit 1
        fi
        ;;
    all)
        if [ "$MODE" == "docker" ]; then
            print_status "Starting all components in Docker..."
            ./docker-run-helper.sh start-all
        else
            print_error "Mode 'all' only supported with --mode docker"
            exit 1
        fi
        ;;
    *)
        print_error "Unknown component: $COMPONENT"
        print_error "Valid components: sensor, edge, all"
        exit 1
        ;;
esac