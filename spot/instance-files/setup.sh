#!/bin/bash
# Main setup script for deployment
# This script runs after the deployment package is extracted

set -e  # Exit on error

echo "Starting amauo deployment setup..."

# First, deploy files from the extracted structure to their proper locations
echo "Deploying files to system locations..."

# Deploy usr files
if [ -d "usr" ]; then
    sudo cp -r usr/* /usr/ 2>/dev/null || true
fi

# Deploy etc files
if [ -d "etc" ]; then
    sudo cp -r etc/* /etc/ 2>/dev/null || true
fi

# Deploy opt files (exclude deployment directory to avoid recursion)
if [ -d "opt" ]; then
    # Copy specific directories to avoid copying deployment directory recursively
    for dir in opt/*/; do
        dirname=$(basename "$dir")
        if [ "$dirname" != "deployment" ]; then
            sudo cp -r "$dir" /opt/ 2>/dev/null || true
        fi
    done
fi

# Set proper permissions for scripts and services (be very specific)
find /usr/local/bin -name "*.py" -exec sudo chmod 755 {} \; 2>/dev/null || true
find /usr/local/bin -name "*.sh" -exec sudo chmod 755 {} \; 2>/dev/null || true

echo "Files deployed successfully"

# Install uv (required for Python scripts) as ubuntu user
if ! sudo -u ubuntu bash -c 'command -v uv' &> /dev/null; then
    echo "Installing uv..."
    sudo -u ubuntu bash -c 'curl -LsSf https://astral.sh/uv/install.sh | sh'
    # Create system-wide symlink for uv so shebangs work
    sudo ln -sf /home/ubuntu/.local/bin/uv /usr/local/bin/uv
    sudo ln -sf /home/ubuntu/.local/bin/uvx /usr/local/bin/uvx
    echo "uv installed successfully and made available system-wide"
else
    echo "uv already installed"
fi

# Install expanso-edge binary if not present
if ! command -v expanso-edge &> /dev/null; then
    echo "Installing expanso-edge..."
    curl -fsSL https://get.expanso.io/edge/install.sh | bash
    echo "expanso-edge installed successfully"
else
    echo "expanso-edge already installed"
fi

# Load expanso-edge environment variables if available
if [ -f /etc/expanso/edge/expanso-edge-env ]; then
    echo "Loading expanso-edge environment variables..."
    set -a
    source /etc/expanso/edge/expanso-edge-env
    set +a
    echo "Bootstrap configuration loaded"
else
    echo "Warning: /etc/expanso/edge/expanso-edge-env not found"
    echo "  expanso-edge will start but won't connect without bootstrap \
credentials"
fi

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    
    # Install GPG tools first to fix verification issues
    sudo apt-get update -qq || true
    sudo apt-get install -y gnupg lsb-release ca-certificates curl || true
    
    # Try the official Docker installation script
    if curl -fsSL https://get.docker.com -o /tmp/get-docker.sh 2>/dev/null; \
        then
        sudo sh /tmp/get-docker.sh 2>/dev/null || {
            echo "Docker script failed, trying alternative installation..."
            # Fallback: install from Ubuntu repositories
            sudo apt-get update -qq || true
            sudo apt-get install -y docker.io docker-compose || true
        }
    else
        echo "Could not download Docker script, using package manager..."
        sudo apt-get update -qq || true
        sudo apt-get install -y docker.io docker-compose || true
    fi
    
    # Configure Docker
    sudo usermod -aG docker ubuntu || true
    sudo systemctl enable docker || true
    sudo systemctl start docker || true
    
    # Clean up
    rm -f /tmp/get-docker.sh
    
    # Verify installation
    if command -v docker &> /dev/null; then
        echo "Docker installed and started successfully"
    else
        echo "Warning: Docker installation may have failed"
    fi
else
    echo "Docker already installed"
fi

# Wait for Docker to be ready
echo "Waiting for Docker to be ready..."
sleep 5

# Set up proper ownership and permissions for data directories
sudo mkdir -p /opt/sensor/config /opt/sensor/logs /opt/sensor/data \
    /opt/sensor/exports
sudo mkdir -p /etc/expanso/edge
sudo mkdir -p /var/lib/expanso/edge
sudo chown -R ubuntu:ubuntu /opt/compose /opt/sensor /etc/expanso \
    /var/lib/expanso 2>/dev/null || true
sudo chmod 755 /opt/sensor /etc/expanso /var/lib/expanso 2>/dev/null || true

# Generate edge configuration if network ID is provided
if [ -f /etc/expanso/edge/network_id ] && [ -f /etc/expanso/edge/config.yaml ]; then
    NETWORK_ID=$(cat /etc/expanso/edge/network_id | tr -d '[:space:]')
    if [ -n "$NETWORK_ID" ]; then
        echo "Generating edge configuration with network ID: $NETWORK_ID"
        sed "s|{{NETWORK_ID}}|$NETWORK_ID|g" /etc/expanso/edge/config.yaml > /tmp/edge-config-generated.yaml
        sudo mv /tmp/edge-config-generated.yaml /etc/expanso/edge/config.yaml
        sudo chown ubuntu:ubuntu /etc/expanso/edge/config.yaml
    fi
fi

# Get instance metadata for node labeling
echo "Retrieving instance metadata..."

# Test metadata service connectivity first
if curl -s --max-time 2 http://169.254.169.254/ > /dev/null 2>&1; then
    echo "DEBUG: EC2 metadata service is accessible"
    INSTANCE_ID=$(curl -s --max-time 5 http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null || echo "")
    REGION=$(curl -s --max-time 5 http://169.254.169.254/latest/meta-data/placement/region 2>/dev/null || echo "")
    
    # Check if we got empty responses
    if [ -z "$INSTANCE_ID" ] || [ "$INSTANCE_ID" = "unknown" ]; then
        echo "WARNING: Could not retrieve instance ID from metadata service"
        INSTANCE_ID=$(hostname)
        echo "INFO: Using hostname as fallback: $INSTANCE_ID"
    fi
    
    if [ -z "$REGION" ] || [ "$REGION" = "unknown" ]; then
        echo "WARNING: Could not retrieve region from metadata service"
        REGION="us-west-2"
        echo "INFO: Using default region: $REGION"
    fi
else
    echo "WARNING: EC2 metadata service is not accessible"
    INSTANCE_ID=$(hostname)
    REGION="us-west-2"
    echo "INFO: Using hostname as fallback: $INSTANCE_ID"
    echo "INFO: Using default region: $REGION"
fi

echo "SUCCESS: Instance ID: $INSTANCE_ID"
echo "SUCCESS: Region: $REGION"

# Generate node identity if the script exists
if [ -x /usr/local/bin/generate_node_identity.py ]; then
    echo "Generating node identity..."
    # Run the script with proper output path (uv should now be available system-wide)
    sudo -u ubuntu /usr/local/bin/generate_node_identity.py -o /opt/sensor/config/node_identity.json
fi

# Start services
echo "Starting services..."

# Start expanso-edge service using systemd
sudo systemctl enable expanso-edge.service 2>/dev/null || true
if sudo systemctl start expanso-edge.service 2>/dev/null; then
    echo "Started expanso-edge.service"
else
    echo "Could not start expanso-edge.service"
fi

# Start sensor service using systemd
sudo systemctl enable sensor.service 2>/dev/null || true
if sudo systemctl start sensor.service 2>/dev/null; then
    echo "Started sensor.service"
else
    echo "Could not start sensor.service"
fi

echo "✅ Amauo deployment setup complete!"

# Create completion marker for deploy_services.py
sudo touch /opt/amauo_setup_complete
sudo chown ubuntu:ubuntu /opt/amauo_setup_complete