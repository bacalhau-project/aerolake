#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests",
# ]
# ///

"""Pipeline metadata generation for audit trail."""

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any


def get_git_sha() -> str:
    """Get current git commit SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except:
        return "unknown"


def get_pipeline_version() -> str:
    """Get pipeline version from environment or default."""
    return os.getenv("PIPELINE_VERSION", "0.9.0")


def generate_transformation_hash(pipeline_type: str, config: Dict[str, Any]) -> str:
    """Generate hash of transformation logic for reproducibility."""
    # Create a deterministic string representation of the transformation
    transformation_def = {
        "pipeline_type": pipeline_type,
        "version": get_pipeline_version(),
        "config_keys": sorted(config.keys()),
    }

    # Create SHA256 hash
    hash_input = json.dumps(transformation_def, sort_keys=True)
    return hashlib.sha256(hash_input.encode()).hexdigest()


def create_pipeline_metadata(
    pipeline_type: str, node_id: str, config: Dict[str, Any]
) -> Dict[str, Any]:
    """Create metadata for pipeline processing audit trail."""
    return {
        "pipeline_version": get_pipeline_version(),
        "pipeline_stage": pipeline_type,
        "processing_timestamp": datetime.now(timezone.utc).isoformat(),
        "git_sha": get_git_sha(),
        "node_id": node_id,
        "transformation_hash": generate_transformation_hash(pipeline_type, config),
    }


def fetch_external_schema(schema_url: str = None) -> Dict[str, Any]:
    """Fetch JSON schema from aerolake.org or use default."""
    import requests

    if schema_url is None:
        # Default to aerolake.org hosted schema
        schema_url = "https://aerolake.org/schemas/wind-turbine-v1.json"

    try:
        response = requests.get(schema_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Warning: Could not fetch external schema from {schema_url}: {e}")
        print("Falling back to local schema file")

        # Fallback to local schema
        local_schema_path = "wind-turbine-schema.json"
        if os.path.exists(local_schema_path):
            with open(local_schema_path) as f:
                return json.load(f)
        else:
            # Return minimal schema if no local file
            return {
                "type": "object",
                "required": ["timestamp", "sensor_id"],
                "properties": {"timestamp": {"type": "string"}, "sensor_id": {"type": "string"}},
            }
