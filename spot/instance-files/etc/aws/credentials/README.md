# AWS Credentials Setup

This directory contains AWS credential files that are deployed to compute instances.

## Required Setup

### 1. Create Real Credentials File

Copy the sample file and add your real AWS credentials:

```bash
cd instance-files/etc/aws/credentials/
cp aws-credentials.sample aws-credentials
# Edit aws-credentials with your real AWS access keys
```

### 2. Update Credentials

Edit `aws-credentials` with your real values:

```ini
[default]
aws_access_key_id = YOUR_REAL_ACCESS_KEY
aws_secret_access_key = YOUR_REAL_SECRET_KEY
region = us-west-2
```

## Deployment

During instance creation, the `aws-credentials` file will be:
1. Copied to `/root/.aws/credentials` (for Bacalhau containers)
2. Copied to `/home/ubuntu/.aws/credentials` (for ubuntu user)

## Security

- ✅ Sample files (*.sample) are committed to git
- ❌ Real credential files are in .gitignore and NEVER committed
- ✅ Credentials are deployed with proper permissions (600)

## Files

- `aws-credentials.sample` - Template with example values
- `aws-credentials` - Your real credentials (create this, never commit)
- `README.md` - This documentation