#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pytest>=7.0",
#   "pytest-mock",
# ]
# ///

"""
Unity Catalog Mapping Tests

Tests that our pipeline data structure correctly maps to Unity Catalog tables
and that metadata fields don't conflict with Databricks Auto Loader processing.
"""

import sys
from pathlib import Path
from unittest.mock import Mock
import pytest

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from test_phase_logic_simple import MockUploader


class TestUnityCatalogMapping:
    """Test Unity Catalog table mapping and metadata compatibility."""

    def test_pipeline_metadata_structure_compatibility(self):
        """Test that pipeline metadata structure is Unity Catalog compatible."""
        uploader = MockUploader("validated")

        sample_data = [{"id": 1, "temperature": 22.5, "humidity": 65.0}]
        valid_records, _ = uploader._validate_and_split_data(sample_data)

        record = valid_records[0]

        # Check pipeline metadata structure
        assert "pipeline_metadata" in record
        metadata = record["pipeline_metadata"]

        # Verify no field name conflicts with Databricks Auto Loader
        # Databricks adds: processing_timestamp (root level)
        # Our metadata has: pipeline_metadata.pipeline_processed_at (nested)
        assert "pipeline_processed_at" in metadata  # Our timestamp field
        assert "processing_timestamp" not in record  # No root level conflict

        # Verify metadata is properly nested to avoid column conflicts
        assert isinstance(metadata, dict)
        assert "stage" in metadata

    def test_databricks_autoloader_column_compatibility(self):
        """Test compatibility with Databricks Auto Loader added columns."""
        uploader = MockUploader("schematized")

        sample_data = [{"id": 1, "temperature": 22.5, "humidity": 65.0}]
        valid_records, _ = uploader._validate_and_split_data(sample_data)

        record = valid_records[0]

        # Reserved Databricks columns that should NOT conflict
        databricks_reserved = [
            "processing_timestamp",  # Added by Auto Loader
            "_metadata",             # Auto Loader file metadata
            "_rescued_data"          # Schema evolution rescue column
        ]

        # Ensure our data doesn't use these reserved names at root level
        for reserved_col in databricks_reserved:
            assert reserved_col not in record

        # Our metadata should be safely nested
        assert "pipeline_metadata" in record
        assert isinstance(record["pipeline_metadata"], dict)

    def test_unity_catalog_table_mapping(self):
        """Test that pipeline types map to correct Unity Catalog tables."""
        # Test the mapping between pipeline bucket types and Unity Catalog tables
        expected_mappings = {
            "ingestion": "sensor_readings_ingestion",
            "validated": "sensor_readings_validated",
            "anomalies": "sensor_readings_anomalies",
            "enriched": "sensor_readings_enriched",  # Note: maps to "schematized" bucket
            "aggregated": "sensor_readings_aggregated"
        }

        # Test that our pipeline bucket mapping aligns with expected UC tables
        uploader = MockUploader("raw")
        pipeline_buckets = uploader.pipeline_bucket_map

        # Verify key mappings exist
        assert "raw" in pipeline_buckets
        assert "validated" in pipeline_buckets
        assert "schematized" in pipeline_buckets
        assert "aggregated" in pipeline_buckets
        assert "anomaly" in pipeline_buckets

        # Verify SPLIT behavior for validated
        assert pipeline_buckets["validated"] == "SPLIT"

    def test_schema_evolution_compatibility(self):
        """Test that our data supports Databricks schema evolution."""
        uploader = MockUploader("validated")

        # Test with data that has extra fields (schema evolution scenario)
        sample_data = [{
            "id": 1,
            "temperature": 22.5,
            "humidity": 65.0,
            "new_field": "future_sensor_data",  # New field not in original schema
            "extra_metadata": {"version": "2.0"}
        }]

        valid_records, _ = uploader._validate_and_split_data(sample_data)
        record = valid_records[0]

        # Verify extra fields are preserved (for schema evolution)
        assert "new_field" in record
        assert "extra_metadata" in record

        # Verify our metadata doesn't interfere
        assert "pipeline_metadata" in record
        metadata = record["pipeline_metadata"]
        assert "stage" in metadata

    def test_json_serialization_compatibility(self):
        """Test that all data types are JSON serializable for S3/Unity Catalog."""
        import json

        uploader = MockUploader("schematized")
        sample_data = [{"id": 1, "temperature": 22.5, "humidity": 65.0}]
        valid_records, _ = uploader._validate_and_split_data(sample_data)

        record = valid_records[0]

        # Should be JSON serializable (required for S3 upload)
        try:
            json_str = json.dumps(record)
            # Should also be deserializable
            deserialized = json.loads(json_str)
            assert deserialized == record
        except (TypeError, ValueError) as e:
            pytest.fail(f"Record is not JSON serializable: {e}")

    def test_metadata_field_naming_conventions(self):
        """Test that metadata fields follow Unity Catalog naming conventions."""
        uploader = MockUploader("validated")
        sample_data = [{"id": 1, "temperature": 22.5, "humidity": 65.0}]
        valid_records, _ = uploader._validate_and_split_data(sample_data)

        metadata = valid_records[0]["pipeline_metadata"]

        # Check field naming conventions (lowercase, underscores)
        for field_name in metadata.keys():
            # Should be lowercase with underscores (Unity Catalog convention)
            assert field_name.islower() or "_" in field_name or field_name.isdigit()
            # Should not contain special characters that cause UC issues
            assert not any(char in field_name for char in ["-", ".", " ", "(", ")"])

    def test_turbine_id_format_compatibility(self):
        """Test that generated turbine_id follows expected schema format."""
        uploader = MockUploader("schematized")
        sample_data = [{"id": 123, "temperature": 22.5, "humidity": 65.0}]
        valid_records, _ = uploader._validate_and_split_data(sample_data)

        record = valid_records[0]

        # Check turbine_id format
        assert "turbine_id" in record
        turbine_id = record["turbine_id"]

        # Should follow the pattern from our transformation
        assert turbine_id.startswith("turbine_")
        assert "123" in turbine_id  # Should include original ID

    def test_required_vs_optional_fields(self):
        """Test that required fields for Unity Catalog are present."""
        uploader = MockUploader("validated")
        sample_data = [{"id": 1, "temperature": 22.5, "humidity": 65.0}]
        valid_records, _ = uploader._validate_and_split_data(sample_data)

        record = valid_records[0]

        # Fields that Unity Catalog will expect based on our schema
        expected_fields = [
            "id",                # Original sensor ID
            "temperature",       # Sensor readings
            "humidity",
            "turbine_id",        # Generated identifier
            "pipeline_metadata"  # Our audit trail
        ]

        for field in expected_fields:
            assert field in record, f"Required field '{field}' missing from record"

    def test_anomaly_record_structure(self):
        """Test that anomaly records have proper structure for Unity Catalog."""
        uploader = MockUploader("validated")

        # Create data that will fail validation
        anomaly_data = [{"id": 1, "temperature": -50.0, "humidity": 150.0}]
        valid_records, invalid_records = uploader._validate_and_split_data(anomaly_data)

        assert len(invalid_records) == 1
        anomaly_record = invalid_records[0]

        # Anomaly records should have same structure as valid records
        assert "turbine_id" in anomaly_record
        assert "pipeline_metadata" in anomaly_record
        assert "temperature" in anomaly_record
        assert "humidity" in anomaly_record

        # Should preserve original anomalous values for analysis
        assert anomaly_record["temperature"] == -50.0
        assert anomaly_record["humidity"] == 150.0

    def test_data_types_unity_catalog_compatible(self):
        """Test that data types are compatible with Unity Catalog Delta tables."""
        uploader = MockUploader("schematized")
        sample_data = [{
            "id": 1,                    # INTEGER
            "temperature": 22.5,        # DOUBLE
            "humidity": 65.0,           # DOUBLE
            "timestamp": "2024-01-15T10:30:00Z",  # STRING (will be parsed as TIMESTAMP)
            "active": True              # BOOLEAN
        }]

        valid_records, _ = uploader._validate_and_split_data(sample_data)
        record = valid_records[0]

        # Check that types are Delta Lake compatible
        assert isinstance(record["id"], int)
        assert isinstance(record["temperature"], (int, float))
        assert isinstance(record["humidity"], (int, float))

        # Metadata should be proper nested structure
        metadata = record["pipeline_metadata"]
        assert isinstance(metadata, dict)
        assert isinstance(metadata["stage"], str)
        assert isinstance(metadata["pipeline_processed_at"], str)


if __name__ == "__main__":
    # Run tests directly
    import subprocess
    result = subprocess.run([
        "python", "-m", "pytest", __file__, "-v", "--tb=short"
    ], cwd=Path(__file__).parent.parent)
    exit(result.returncode)