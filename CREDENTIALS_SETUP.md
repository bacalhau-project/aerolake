# Credentials Setup Guide

This guide explains how to set up credentials for the Databricks Wind Turbine Pipeline.

## ⚠️ Security Notice

**NEVER commit actual credentials to git!** All credential files are excluded by `.gitignore`.

## Required Credential Files

### 1. Main Credentials (`credentials/expanso-s3-env.sh`)

Copy the sample and fill in your AWS credentials:

```bash
cp credentials/expanso-s3-env.sh.sample credentials/expanso-s3-env.sh
# Edit credentials/expanso-s3-env.sh with your actual AWS keys
```

### 2. Instance Deployment Credentials (`spot/instance-files/etc/aws/credentials/`)

For EC2 instance deployment:

```bash
# Copy samples and configure
cp spot/instance-files/etc/aws/credentials/expanso-s3-env.sh.sample \
   spot/instance-files/etc/aws/credentials/expanso-s3-env.sh

cp spot/instance-files/etc/aws/credentials/aws-credentials.sample \
   spot/instance-files/etc/aws/credentials/aws-credentials
```

### 3. Instance Configuration (`spot/instances.json`)

```bash
cp spot/instances.json.sample spot/instances.json
# Edit with your actual EC2 instance details
```

## Required AWS Permissions

Your AWS credentials need access to:
- S3 bucket operations (read/write)
- EC2 instance management
- Databricks Unity Catalog operations

## Environment Variables

The following environment variables can override credential file locations:

- `SQLITE_DB_PATH`: Path to sensor database
- `AWS_CREDENTIALS_DIR`: Directory containing credential files
- `AWS_REGION`: AWS region (defaults to us-west-2)

## Verification

Test your credentials:

```bash
# Test AWS access
aws sts get-caller-identity

# Test local uploader
cd databricks-uploader
uv run sqlite_to_databricks_uploader.py --config databricks-s3-uploader-config-local.yaml --dry-run

# Test Bacalhau job
bacalhau job run jobs/databricks-uploader-job.yaml
```

## Troubleshooting

If you see "AWS credentials are REQUIRED" errors:

1. Check that credential files exist and have correct format
2. Verify AWS keys have necessary permissions
3. Ensure file permissions are readable (644)
4. Check that paths in configuration match actual file locations