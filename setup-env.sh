#!/bin/bash

# =============================================================================
# ENVIRONMENT SETUP HELPER SCRIPT
# =============================================================================
# This script helps you configure your .env file step by step

set -e

ENV_FILE=".env"
EXAMPLE_FILE=".env.example"

echo "🚀 Setting up your Databricks Wind Turbine Pipeline Environment"
echo "=============================================================="

# Check if .env exists
if [[ ! -f "$ENV_FILE" ]]; then
    echo "❌ .env file not found. Please run this from the project root directory."
    exit 1
fi

echo ""
echo "📋 I'll help you fill in the required values step by step."
echo "💡 You can press ENTER to skip values you want to set manually later."
echo ""

# Helper function to prompt for values
prompt_for_value() {
    local var_name=$1
    local description=$2
    local current_value=$3
    local example=$4
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔧 Setting: $var_name"
    echo "📝 Description: $description"
    if [[ -n "$example" ]]; then
        echo "📄 Example: $example"
    fi
    if [[ -n "$current_value" && "$current_value" != *"YOUR_"* && "$current_value" != *"_HERE"* ]]; then
        echo "✅ Current value: $current_value"
        read -p "Keep this value? (y/n): " keep_value
        if [[ $keep_value == "y" || $keep_value == "Y" || $keep_value == "" ]]; then
            return
        fi
    fi
    
    echo "🖊️  Current: $current_value"
    read -p "New value (or ENTER to skip): " new_value
    
    if [[ -n "$new_value" ]]; then
        # Escape special characters for sed
        escaped_current=$(printf '%s\n' "$current_value" | sed 's/[[\.*^$()+?{|]/\\&/g')
        escaped_new=$(printf '%s\n' "$new_value" | sed 's/[[\.*^$()+?{|]/\\&/g')
        sed -i.bak "s|$var_name=$escaped_current|$var_name=$escaped_new|g" "$ENV_FILE"
        echo "✅ Updated $var_name"
    else
        echo "⏭️  Skipped $var_name"
    fi
    echo ""
}

# Get current values from .env
get_env_value() {
    grep "^$1=" "$ENV_FILE" | cut -d'=' -f2- | sed 's/^"//' | sed 's/"$//'
}

echo "🔍 Checking your current configuration..."
echo ""

# AWS Configuration
echo "🏗️  AWS CONFIGURATION"
prompt_for_value "AWS_ACCOUNT_ID" "Your AWS Account ID (12-digit number)" "$(get_env_value 'AWS_ACCOUNT_ID')" "123456789012"

echo "💡 AWS Credentials: You can set these here OR use AWS profiles/roles"
prompt_for_value "AWS_ACCESS_KEY_ID" "AWS Access Key ID (optional if using IAM roles)" "$(get_env_value 'AWS_ACCESS_KEY_ID')" "AKIAIOSFODNN7EXAMPLE"
prompt_for_value "AWS_SECRET_ACCESS_KEY" "AWS Secret Access Key (optional if using IAM roles)" "$(get_env_value 'AWS_SECRET_ACCESS_KEY')" "wJalrXUtnFEMI/K7MDENG/bPxRfiCYzEXAMPLEKEY"

# Databricks Configuration
echo "🧱 DATABRICKS CONFIGURATION"
prompt_for_value "DATABRICKS_HOST" "Your Databricks workspace URL (without https://)" "$(get_env_value 'DATABRICKS_HOST')" "your-workspace.cloud.databricks.com"
prompt_for_value "DATABRICKS_TOKEN" "Databricks Personal Access Token (starts with dapi-)" "$(get_env_value 'DATABRICKS_TOKEN')" "dapi-abc123def456..."
prompt_for_value "DATABRICKS_HTTP_PATH" "SQL Warehouse/Cluster HTTP Path" "$(get_env_value 'DATABRICKS_HTTP_PATH')" "/sql/1.0/endpoints/abc123def456"

# GitHub Configuration  
echo "🐙 GITHUB CONFIGURATION"
prompt_for_value "GITHUB_TOKEN" "GitHub Personal Access Token (starts with ghp_)" "$(get_env_value 'GITHUB_TOKEN')" "ghp_abc123def456..."

echo ""
echo "🎉 Configuration complete!"
echo ""

# Test the configuration
echo "🧪 Testing your configuration..."
echo ""

# Load the updated .env
set -a
source "$ENV_FILE"
set +a

# Test AWS
echo "Testing AWS connection..."
if command -v aws &> /dev/null; then
    if aws sts get-caller-identity &> /dev/null; then
        echo "✅ AWS connection successful"
        echo "   Account: $(aws sts get-caller-identity --query Account --output text)"
        echo "   Region: $AWS_REGION"
    else
        echo "⚠️  AWS connection failed. Check your credentials."
    fi
else
    echo "⚠️  AWS CLI not installed. Cannot test AWS connection."
fi

echo ""

# Test S3 buckets
echo "Testing S3 bucket access..."
if aws s3 ls s3://$S3_BUCKET_RAW/ &> /dev/null; then
    echo "✅ S3 bucket access successful: $S3_BUCKET_RAW"
else
    echo "⚠️  Cannot access S3 bucket: $S3_BUCKET_RAW"
fi

echo ""

# Test Databricks (simple)
if [[ -n "$DATABRICKS_HOST" && "$DATABRICKS_HOST" != *"YOUR_"* ]]; then
    echo "Testing Databricks connection..."
    if curl -s --connect-timeout 5 "https://$DATABRICKS_HOST" > /dev/null; then
        echo "✅ Databricks host reachable: $DATABRICKS_HOST"
    else
        echo "⚠️  Cannot reach Databricks host: $DATABRICKS_HOST"
    fi
else
    echo "⏭️  Skipping Databricks test (host not configured)"
fi

echo ""
echo "🎯 Next Steps:"
echo "1. Review your .env file: cat .env"
echo "2. Test edge processing: expanso job run jobs/edge-processing-job.yaml --template-vars pipeline_type=validated --force"
echo "3. Monitor edge nodes: expanso node list"
echo ""
echo "📚 For more help, see: docs/ENVIRONMENT_SETUP.md"
echo "🐛 If you encounter issues, check: docs/DEVELOPMENT_RULES.md"

# Backup original
if [[ -f "$ENV_FILE.bak" ]]; then
    rm "$ENV_FILE.bak"
fi