# Expanso Edge Bootstrap Configuration

This directory contains configuration files for Expanso Edge bootstrap.

## Setup

1. Copy the sample environment file:
   ```bash
   cp expanso-edge-env.sample expanso-edge-env
   ```

2. Edit `expanso-edge-env` with your bootstrap credentials:
   - `EXPANSO_EDGE_BOOTSTRAP_TOKEN`: Your bootstrap token from \
https://dev-cloud.expanso.dev
   - `EXPANSO_EDGE_BOOTSTRAP_URL`: The bootstrap URL (currently \
`https://start.dev-cloud.expanso.dev`)

## Bootstrap Options

### Using Environment Variables (Recommended for systemd)
```bash
export EXPANSO_EDGE_BOOTSTRAP_TOKEN=<token>
export EXPANSO_EDGE_BOOTSTRAP_URL=https://start.dev-cloud.expanso.dev
expanso-edge run
```

### Using Command Line Flags
```bash
expanso-edge run --bootstrap-token=<token> \
    --bootstrap-url=https://start.dev-cloud.expanso.dev
```

## Data Directory

The data directory is `/var/lib/expanso/edge` and contains:
- Node identity
- Registration configuration (created at \
`/var/lib/expanso/edge/config.d/50-registration.yaml`)
- Credentials

Registration creates a config file like:
```yaml
orchestrator:
    node_id: 6d601d5e-1694-472b-8b7c-668829035638
    credentials_path: /var/lib/expanso/edge/auth/<node_id>.creds
    address: <network_id>.us1.dev-cloud.expanso.dev
    require_tls: true
```

## CLI Usage

After nodes are registered, you can manage them using the Expanso CLI:

```bash
# Create a profile
expanso-cli profile save demo \
    --endpoint https://<NETWORK_ID>.us1.dev-cloud.expanso.dev:9010

# Use the profile
expanso-cli -p demo node ls

# Make it default
expanso-cli profile select demo
expanso-cli node ls
```

Note: HTTP endpoints are currently not secured and are publicly accessible.

## Important Notes

- Never commit `expanso-edge-env` to git - it contains secrets
- Keep only `.sample` files in version control
- The systemd service automatically loads environment variables from \
`expanso-edge-env`
