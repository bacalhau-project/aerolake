#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pytest>=7.0",
#   "pytest-mock",
#   "pydantic>=2.0.0",
#   "jsonschema>=4.0.0",
#   "pyyaml>=6.0",
#   "python-dateutil>=2.8",
#   "boto3>=1.26.0",
#   "requests>=2.31.0",
# ]
# ///

"""
Phase Routing Unit Tests for Databricks Uploader

Tests the pipeline phase logic to ensure each phase correctly:
1. Loads the proper pipeline configuration
2. Processes input data according to phase rules
3. Routes output to the correct bucket (without actually uploading)
4. Handles data validation and splitting appropriately

Pipeline Phases Tested:
- raw: No processing, all data → ingestion bucket
- schematized: Transform to turbine schema → schematized bucket
- validated: External schema validation → validated bucket (valid) + anomalies bucket (invalid)
- aggregated: Basic aggregation → aggregated bucket
- anomaly: Direct to anomaly bucket
"""

import json
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple
from unittest.mock import Mock, patch, MagicMock
import pytest
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import uploader components
from sqlite_to_databricks_uploader import SQLiteToS3Uploader
from pipeline_manager import PipelineManager


class TestPhaseRouting:
    """Test pipeline phase routing logic without actual S3 uploads."""

    @pytest.fixture
    def sample_sensor_data(self):
        """Sample environmental sensor data for testing."""
        return [
            {
                "id": 1,
                "timestamp": "2024-01-15T10:30:00Z",
                "sensor_type": "environmental",
                "temperature": 22.5,
                "humidity": 65.0,
                "pressure": 1013.25,
                "voltage": 12.1,
                "vibration": 2.3,
                "location": "turbine_001"
            },
            {
                "id": 2,
                "timestamp": "2024-01-15T10:31:00Z",
                "sensor_type": "environmental",
                "temperature": -50.0,  # Anomaly: too cold
                "humidity": 45.0,
                "pressure": 1015.0,
                "voltage": 12.0,
                "vibration": 1.8,
                "location": "turbine_002"
            },
            {
                "id": 3,
                "timestamp": "2024-01-15T10:32:00Z",
                "sensor_type": "environmental",
                "temperature": 25.0,
                "humidity": 120.0,  # Anomaly: humidity > 100%
                "pressure": 1012.0,
                "voltage": 11.9,
                "vibration": 2.1,
                "location": "turbine_003"
            }
        ]

    @pytest.fixture
    def temp_config(self):
        """Create temporary configuration for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            # Create a proper temporary directory for state
            temp_state_dir = tempfile.mkdtemp()
            config = {
                'sqlite': '/tmp/test_sensor.db',
                'sqlite_table': 'sensor_readings',
                'upload_interval': 30,
                'state_dir': temp_state_dir,
                'schema_url': 'https://example.com/schema.json',
                's3_configuration': {
                    'region': 'us-west-2',
                    'access_key_id': 'test_access_key',
                    'secret_access_key': 'test_secret_key',
                    'buckets': {
                        'ingestion': 'test-raw-data-us-west-2',
                        'validated': 'test-validated-data-us-west-2',
                        'anomalies': 'test-anomalies-data-us-west-2',
                        'schematized': 'test-schematized-data-us-west-2',
                        'aggregated': 'test-aggregated-data-us-west-2',
                        'enriched': 'test-enriched-data-us-west-2'
                    }
                }
            }
            import yaml
            yaml.dump(config, f)
            yield f.name
            Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def temp_pipeline_db(self):
        """Create temporary pipeline database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            yield f.name
            Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def mock_uploader(self, temp_config, temp_pipeline_db):
        """Create uploader instance with mocked S3 operations."""
        # Create temporary state directory
        state_dir = Path(tempfile.mkdtemp())

        with patch.dict('os.environ', {
            'PIPELINE_CONFIG_DB': temp_pipeline_db,
            'STATE_DIR': str(state_dir)
        }):
            with patch('sqlite_to_databricks_uploader.SQLiteToS3Uploader._upload_to_s3') as mock_upload:
                with patch('sqlite_to_databricks_uploader.SQLiteToS3Uploader._load_node_identity') as mock_identity:
                    with patch('sqlite_to_databricks_uploader.SQLiteToS3Uploader._validate_sqlite_access') as mock_sqlite:
                        with patch('sqlite_to_databricks_uploader.SQLiteToS3Uploader._print_initial_bucket_scan') as mock_scan:
                            mock_identity.return_value = 'test-node-001'
                            mock_upload.return_value = True
                            mock_sqlite.return_value = None  # No error
                            mock_scan.return_value = None

                            uploader = SQLiteToS3Uploader(temp_config, verbose=True)
                            uploader.state_dir = state_dir
                            yield uploader

    def set_pipeline_type(self, uploader, pipeline_type: str):
        """Helper to set pipeline type for testing."""
        uploader.pipeline_manager.set_pipeline_type(pipeline_type, "test_runner")
        # Reload configuration
        pipeline_config = uploader.pipeline_manager.get_current_config()
        uploader.current_pipeline_type = pipeline_config["type"]

    def test_raw_phase_routing(self, mock_uploader, sample_sensor_data):
        """Test raw phase: no processing, all data goes to ingestion bucket."""
        # Set pipeline to raw mode
        self.set_pipeline_type(mock_uploader, "raw")

        # Process data
        valid_records, invalid_records = mock_uploader._validate_and_split_data(sample_sensor_data)

        # In raw mode, all data should be valid (no processing)
        assert len(valid_records) == 3
        assert len(invalid_records) == 0

        # Data should be unchanged
        assert valid_records == sample_sensor_data

        # Should route to ingestion bucket
        expected_bucket = mock_uploader.pipeline_bucket_map["raw"]
        assert expected_bucket == "ingestion"

    def test_schematized_phase_routing(self, mock_uploader, sample_sensor_data):
        """Test schematized phase: transform to turbine schema, no validation."""
        self.set_pipeline_type(mock_uploader, "schematized")

        # Mock the schema transformation
        with patch.object(mock_uploader, '_map_to_turbine_schema') as mock_transform:
            with patch('pipeline_metadata.create_pipeline_metadata') as mock_metadata:
                mock_metadata.return_value = {"pipeline_stage": "schematized", "timestamp": "2024-01-15T10:30:00Z"}

                # Mock transformation to return structured data
                def mock_transform_func(record):
                    return {
                        "timestamp": record["timestamp"],
                        "turbine_id": f"turbine_{record['id']}",
                        "site_id": "test_site",
                        "temperature": record["temperature"],
                        "humidity": record["humidity"],
                        "pressure": record["pressure"],
                        "wind_speed": 15.0,  # Derived field
                        "power_output": 1500.0  # Derived field
                    }
                mock_transform.side_effect = mock_transform_func

                valid_records, invalid_records = mock_uploader._validate_and_split_data(sample_sensor_data)

                # In schematized mode, all data should be valid (no validation, only transformation)
                assert len(valid_records) == 3
                assert len(invalid_records) == 0

                # Check that data was transformed
                for record in valid_records:
                    assert "turbine_id" in record
                    assert "wind_speed" in record
                    assert "pipeline_metadata" in record

                # Should route to schematized bucket
                expected_bucket = mock_uploader.pipeline_bucket_map["schematized"]
                assert expected_bucket == "schematized"

    def test_validated_phase_routing(self, mock_uploader, sample_sensor_data):
        """Test validated phase: external schema validation with splitting."""
        self.set_pipeline_type(mock_uploader, "validated")

        # Mock external dependencies
        mock_schema = {
            "type": "object",
            "required": ["timestamp", "turbine_id", "temperature", "humidity"],
            "properties": {
                "temperature": {"type": "number", "minimum": -20, "maximum": 60},
                "humidity": {"type": "number", "minimum": 0, "maximum": 100}
            }
        }

        with patch.object(mock_uploader, '_map_to_turbine_schema') as mock_transform:
            with patch('pipeline_metadata.create_pipeline_metadata') as mock_metadata:
                with patch('pipeline_metadata.fetch_external_schema') as mock_fetch_schema:
                    with patch('jsonschema.validate') as mock_validate:

                        mock_metadata.return_value = {"pipeline_stage": "validated"}
                        mock_fetch_schema.return_value = mock_schema

                        # Mock transformation
                        def mock_transform_func(record):
                            return {
                                "timestamp": record["timestamp"],
                                "turbine_id": f"turbine_{record['id']}",
                                "temperature": record["temperature"],
                                "humidity": record["humidity"]
                            }
                        mock_transform.side_effect = mock_transform_func

                        # Mock validation to fail on anomalous data
                        def mock_validate_func(record, schema):
                            if record["temperature"] < -20 or record["temperature"] > 60:
                                from jsonschema import ValidationError
                                raise ValidationError("Temperature out of range")
                            if record["humidity"] < 0 or record["humidity"] > 100:
                                from jsonschema import ValidationError
                                raise ValidationError("Humidity out of range")

                        mock_validate.side_effect = mock_validate_func

                        valid_records, invalid_records = mock_uploader._validate_and_split_data(sample_sensor_data)

                        # Should have 1 valid record and 2 invalid (temperature & humidity anomalies)
                        assert len(valid_records) == 1
                        assert len(invalid_records) == 2

                        # Check that invalid records have validation error info
                        for invalid_record in invalid_records:
                            assert "validation_error" in invalid_record
                            assert "validation_path" in invalid_record

                        # Should use SPLIT routing (validated for valid, anomalies for invalid)
                        expected_bucket = mock_uploader.pipeline_bucket_map["validated"]
                        assert expected_bucket == "SPLIT"

    def test_aggregated_phase_routing(self, mock_uploader, sample_sensor_data):
        """Test aggregated phase: basic aggregation to aggregated bucket."""
        self.set_pipeline_type(mock_uploader, "aggregated")

        # For aggregated mode, it should pass through like raw (in current implementation)
        valid_records, invalid_records = mock_uploader._validate_and_split_data(sample_sensor_data)

        # Should pass through unchanged (current implementation)
        assert len(valid_records) == 3
        assert len(invalid_records) == 0
        assert valid_records == sample_sensor_data

        # Should route to aggregated bucket
        expected_bucket = mock_uploader.pipeline_bucket_map["aggregated"]
        assert expected_bucket == "aggregated"

    def test_anomaly_phase_routing(self, mock_uploader, sample_sensor_data):
        """Test anomaly phase: direct routing to anomalies bucket."""
        self.set_pipeline_type(mock_uploader, "anomaly")

        valid_records, invalid_records = mock_uploader._validate_and_split_data(sample_sensor_data)

        # Should pass through unchanged (current implementation)
        assert len(valid_records) == 3
        assert len(invalid_records) == 0

        # Should route to anomalies bucket
        expected_bucket = mock_uploader.pipeline_bucket_map["anomaly"]
        assert expected_bucket == "anomalies"

    def test_bucket_mapping_completeness(self, mock_uploader):
        """Test that all pipeline types have proper bucket mappings."""
        expected_pipeline_types = ["raw", "schematized", "validated", "aggregated", "anomaly"]

        for pipeline_type in expected_pipeline_types:
            assert pipeline_type in mock_uploader.pipeline_bucket_map
            bucket = mock_uploader.pipeline_bucket_map[pipeline_type]
            assert bucket in ["ingestion", "schematized", "validated", "anomalies", "aggregated", "SPLIT"]

    def test_pipeline_type_switching(self, mock_uploader, sample_sensor_data):
        """Test dynamic pipeline type switching during runtime."""
        # Start with raw
        self.set_pipeline_type(mock_uploader, "raw")
        assert mock_uploader.current_pipeline_type == "raw"

        # Switch to validated
        self.set_pipeline_type(mock_uploader, "validated")
        assert mock_uploader.current_pipeline_type == "validated"

        # Switch to schematized
        self.set_pipeline_type(mock_uploader, "schematized")
        assert mock_uploader.current_pipeline_type == "schematized"

        # Verify the bucket mapping changes appropriately
        raw_bucket = mock_uploader.pipeline_bucket_map["raw"]
        validated_bucket = mock_uploader.pipeline_bucket_map["validated"]
        schematized_bucket = mock_uploader.pipeline_bucket_map["schematized"]

        assert raw_bucket == "ingestion"
        assert validated_bucket == "SPLIT"
        assert schematized_bucket == "schematized"

    def test_invalid_pipeline_type_handling(self, mock_uploader):
        """Test handling of invalid/unknown pipeline types."""
        # Test with unknown pipeline type
        mock_uploader.current_pipeline_type = "unknown_type"

        # Should default gracefully (pass-through behavior)
        sample_data = [{"id": 1, "timestamp": "2024-01-15T10:30:00Z", "temperature": 25.0}]
        valid_records, invalid_records = mock_uploader._validate_and_split_data(sample_data)

        # Should pass through unchanged for unknown types
        assert len(valid_records) == 1
        assert len(invalid_records) == 0
        assert valid_records == sample_data

    @pytest.mark.parametrize("pipeline_type,expected_bucket", [
        ("raw", "ingestion"),
        ("ingestion", "ingestion"),
        ("schematized", "schematized"),
        ("validated", "SPLIT"),
        ("anomaly", "anomalies"),
        ("anomalies", "anomalies"),
        ("aggregated", "aggregated"),
        ("enriched", "enriched"),
        ("filtered", "enriched"),
    ])
    def test_all_pipeline_bucket_mappings(self, mock_uploader, pipeline_type, expected_bucket):
        """Test all defined pipeline type to bucket mappings."""
        actual_bucket = mock_uploader.pipeline_bucket_map.get(pipeline_type)
        assert actual_bucket == expected_bucket, f"Pipeline type '{pipeline_type}' should map to '{expected_bucket}', got '{actual_bucket}'"


if __name__ == "__main__":
    # Run tests directly
    import subprocess
    result = subprocess.run([
        "python", "-m", "pytest", __file__, "-v", "--tb=short"
    ], cwd=Path(__file__).parent.parent)
    exit(result.returncode)