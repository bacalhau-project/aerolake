#!/bin/bash

# Diagnostic script for EC2 metadata service
echo "=== EC2 Metadata Service Diagnostic ==="
echo "Date: $(date)"
echo

# Check if we're on EC2 by looking for EC2-specific files
echo "1. Checking for EC2 indicators:"
if [ -f /sys/hypervisor/uuid ] && grep -qi ec2 /sys/hypervisor/uuid 2>/dev/null; then
    echo "   ✓ Running on EC2 (hypervisor UUID found)"
else
    echo "   ✗ Not on EC2 or hypervisor UUID not found"
fi

if [ -f /sys/devices/virtual/dmi/id/product_uuid ]; then
    echo "   Product UUID: $(cat /sys/devices/virtual/dmi/id/product_uuid 2>/dev/null || echo 'not readable')"
fi

echo
echo "2. Testing IMDSv1 (direct access):"
echo -n "   Instance ID: "
curl -s --max-time 2 http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null || echo "FAILED"

echo
echo "3. Testing IMDSv2 (token-based):"
echo -n "   Getting token... "
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" \
    --max-time 2 -s 2>/dev/null)

if [ -n "$TOKEN" ]; then
    echo "SUCCESS"
    echo -n "   Instance ID with token: "
    curl -H "X-aws-ec2-metadata-token: $TOKEN" \
        --max-time 2 -s \
        http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null || echo "FAILED"
else
    echo "FAILED"
fi

echo
echo "4. Network connectivity to metadata service:"
echo -n "   Ping 169.254.169.254: "
ping -c 1 -W 1 169.254.169.254 &>/dev/null && echo "SUCCESS" || echo "FAILED"

echo
echo "5. Route to metadata service:"
ip route get 169.254.169.254 2>/dev/null || echo "   No route found"

echo
echo "6. Checking iptables rules that might block metadata:"
sudo iptables -L -n 2>/dev/null | grep -E "169.254.169.254|DROP|REJECT" || echo "   No blocking rules found"

echo
echo "7. Testing with wget (alternative to curl):"
echo -n "   Instance ID via wget: "
wget -q -O - --timeout=2 http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null || echo "FAILED"

echo
echo "8. Check if metadata endpoint is disabled in instance settings:"
echo "   Note: If all tests fail, the instance might have:"
echo "   - IMDSv2 enforced (HttpTokens=required)"
echo "   - Metadata disabled (HttpEndpoint=disabled)"
echo "   - Network/firewall blocking metadata service"

echo
echo "9. Environment variables:"
env | grep -E "AWS|EC2|INSTANCE" || echo "   No relevant environment variables found"

echo
echo "=== End Diagnostic ==="