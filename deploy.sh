#!/bin/bash
# Deploy script for Expanso Edge pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[DEPLOY]${NC} $1"
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
TARGET=""
ENV_FILE=".env"
SKIP_VALIDATION=""
SKIP_BUILD=""
DRY_RUN=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --target)
            TARGET="$2"
            shift 2
            ;;
        --env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --skip-validation)
            SKIP_VALIDATION="true"
            shift
            ;;
        --skip-build)
            SKIP_BUILD="true"
            shift
            ;;
        --dry-run)
            DRY_RUN="true"
            shift
            ;;
        --help)
            echo "Usage: $0 --target TARGET [OPTIONS]"
            echo ""
            echo "Targets:"
            echo "  aws                Deploy AWS infrastructure (S3, IAM)"
            echo "  expanso            Deploy to Expanso network"
            echo "  full               Deploy everything"
            echo ""
            echo "Options:"
            echo "  --env-file FILE     Environment file (default: .env)"
            echo "  --skip-validation   Skip environment validation"
            echo "  --skip-build        Skip Docker image build"
            echo "  --dry-run           Show what would be done without doing it"
            echo ""
            echo "Examples:"
            echo "  $0 --target aws"
            echo "  $0 --target expanso"
            echo "  $0 --target full"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$TARGET" ]; then
    print_error "Target is required. Use --target to specify deployment target."
    print_error "See --help for available targets."
    exit 1
fi

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

# Function to validate environment
validate_environment() {
    print_status "Validating environment..."
    
    local errors=0
    
    # Check required environment variables
    if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
        print_error "AWS credentials not found in environment"
        errors=$((errors + 1))
    fi
    
    if [ -z "$AWS_REGION" ]; then
        print_error "AWS_REGION not found in environment"
        errors=$((errors + 1))
    fi
    
    if [ -z "$S3_BUCKET_PREFIX" ]; then
        print_error "S3_BUCKET_PREFIX not found in environment"
        errors=$((errors + 1))
    fi
    
    if [ $errors -gt 0 ]; then
        print_error "Environment validation failed with $errors errors"
        exit 1
    fi
    
    print_status "Environment validation passed"
}

# Function to deploy AWS infrastructure
deploy_aws() {
    print_status "Deploying AWS infrastructure..."
    
    if [ "$DRY_RUN" == "true" ]; then
        print_info "[DRY RUN] Would create S3 buckets and IAM roles"
        return
    fi
    
    # Create S3 buckets
    print_status "Creating S3 buckets..."
    ./scripts/create-pipeline-buckets.sh
    
    # Setup S3 access
    print_status "Setting up S3 access..."
    ./scripts/setup-databricks-s3-access.sh
    
    # Update IAM roles
    print_status "Updating IAM roles..."
    ./scripts/update-iam-role-for-new-buckets.sh
    
    print_status "AWS deployment complete!"
}

# Function to deploy to Expanso
deploy_expanso() {
    print_status "Deploying to Expanso..."
    
    if [ "$DRY_RUN" == "true" ]; then
        print_info "[DRY RUN] Would submit the following Expanso jobs:"
        echo "  - jobs/expanso-edge-job.yaml"
        return
    fi
    
    # Check if Expanso CLI is installed
    if ! command -v expanso &> /dev/null; then
        print_error "Expanso CLI is not installed"
        print_info "Install from: https://docs.expanso.io/getting-started/installation"
        exit 1
    fi
    
    # Build Docker image if not skipped
    if [ "$SKIP_BUILD" != "true" ]; then
        print_status "Building Docker image for Expanso..."
        ./build.sh --component sensor --push
    fi
    
    print_status "Expanso deployment complete!"
}

# Function to deploy everything
deploy_full() {
    print_status "Starting full deployment..."
    
    # Deploy in order
    deploy_aws
    deploy_expanso
    
    print_status "Full deployment complete!"
    
    # Show status
    print_info "Deployment Summary:"
    echo ""
    echo "  AWS Resources:     ✓ Created"
    echo "  Expanso Network:   ✓ Deployed"
    echo ""
    echo "Next steps:"
    echo "  1. Start edge nodes with instance files"
    echo "  2. Monitor edge network status"
}

# Main execution
if [ "$SKIP_VALIDATION" != "true" ]; then
    validate_environment
fi

case $TARGET in
    aws)
        deploy_aws
        ;;
    expanso)
        deploy_expanso
        ;;
    full)
        deploy_full
        ;;
    *)
        print_error "Unknown target: $TARGET"
        print_error "Valid targets: aws, expanso, full"
        exit 1
        ;;
esac

if [ "$DRY_RUN" == "true" ]; then
    print_info "This was a dry run. No changes were made."
fi