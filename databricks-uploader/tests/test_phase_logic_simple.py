#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pytest>=7.0",
#   "pytest-mock",
# ]
# ///

"""
Simplified Phase Logic Tests

Tests just the core validation logic without full uploader initialization.
This isolates the phase routing behavior for testing.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

class MockUploader:
    """Simplified mock uploader for testing phase logic only."""

    def __init__(self, pipeline_type="raw"):
        self.current_pipeline_type = pipeline_type
        self.pipeline_bucket_map = {
            "raw": "ingestion",
            "ingestion": "ingestion",
            "schematized": "schematized",
            "validated": "SPLIT",
            "anomaly": "anomalies",
            "anomalies": "anomalies",
            "aggregated": "aggregated",
            "enriched": "enriched",
            "filtered": "enriched",
        }
        self.config = {"schema_url": "https://example.com/schema.json"}
        self.node_id = "test-node-001"

    def _validate_and_split_data(self, data):
        """
        Simplified version of the validation logic for testing.
        This mimics the actual uploader behavior without external dependencies.
        """
        valid_records = []
        invalid_records = []

        for record in data:
            if self.current_pipeline_type == "raw":
                # Raw: no processing, all records are valid
                valid_records.append(record)

            elif self.current_pipeline_type == "schematized":
                # Schematized: transform but don't validate (mock transformation)
                transformed_record = self._mock_transform_to_turbine_schema(record)
                valid_records.append(transformed_record)

            elif self.current_pipeline_type == "validated":
                # Validated: apply validation rules and split
                transformed_record = self._mock_transform_to_turbine_schema(record)
                if self._mock_validate_record(transformed_record):
                    valid_records.append(transformed_record)
                else:
                    invalid_records.append(transformed_record)

            elif self.current_pipeline_type == "aggregated":
                # Aggregated: basic processing
                valid_records.append(record)

            elif self.current_pipeline_type == "anomaly":
                # Anomaly: direct to anomaly bucket
                valid_records.append(record)

            else:
                # Unknown type: pass through
                valid_records.append(record)

        return valid_records, invalid_records

    def _mock_transform_to_turbine_schema(self, record):
        """Mock transformation to turbine schema."""
        return {
            "timestamp": record.get("timestamp"),
            "turbine_id": f"turbine_{record.get('id', '001')}",
            "site_id": "test_site",
            "temperature": record.get("temperature"),
            "humidity": record.get("humidity"),
            "pressure": record.get("pressure", 1013.25),
            "wind_speed": 15.0,
            "power_output": 1500.0,
            "pipeline_metadata": {
                "stage": self.current_pipeline_type,
                "processed_at": "2024-01-15T10:30:00Z"
            }
        }

    def _mock_validate_record(self, record):
        """Mock validation with simple rules that match our test data."""
        temp = record.get("temperature", 0)
        humidity = record.get("humidity", 0)

        # Handle invalid data types and None values
        try:
            temp = float(temp) if temp is not None else 0.0
        except (ValueError, TypeError):
            temp = 0.0

        try:
            humidity = float(humidity) if humidity is not None else 0.0
        except (ValueError, TypeError):
            humidity = 0.0

        # Simple validation rules
        if temp < -20 or temp > 60:
            return False
        if humidity < 0 or humidity > 100:
            return False

        return True


class TestPhaseLogicSimple:
    """Simplified tests for phase logic without S3 dependencies."""

    @pytest.fixture
    def sample_data(self):
        """Sample sensor data for testing."""
        return [
            {
                "id": 1,
                "timestamp": "2024-01-15T10:30:00Z",
                "temperature": 22.5,
                "humidity": 65.0,
                "location": "turbine_001"
            },
            {
                "id": 2,
                "timestamp": "2024-01-15T10:31:00Z",
                "temperature": -50.0,  # Anomaly: too cold
                "humidity": 45.0,
                "location": "turbine_002"
            },
            {
                "id": 3,
                "timestamp": "2024-01-15T10:32:00Z",
                "temperature": 25.0,
                "humidity": 120.0,  # Anomaly: humidity > 100%
                "location": "turbine_003"
            }
        ]

    def test_raw_phase_logic(self, sample_data):
        """Test raw phase: no processing, all data passes through."""
        uploader = MockUploader("raw")
        valid, invalid = uploader._validate_and_split_data(sample_data)

        assert len(valid) == 3
        assert len(invalid) == 0
        assert valid == sample_data  # No transformation

        # Check bucket mapping
        assert uploader.pipeline_bucket_map["raw"] == "ingestion"

    def test_schematized_phase_logic(self, sample_data):
        """Test schematized phase: transform but don't validate."""
        uploader = MockUploader("schematized")
        valid, invalid = uploader._validate_and_split_data(sample_data)

        assert len(valid) == 3
        assert len(invalid) == 0

        # Check transformation occurred
        for record in valid:
            assert "turbine_id" in record
            assert "wind_speed" in record
            assert "pipeline_metadata" in record

        # Check bucket mapping
        assert uploader.pipeline_bucket_map["schematized"] == "schematized"

    def test_validated_phase_logic(self, sample_data):
        """Test validated phase: validate and split records."""
        uploader = MockUploader("validated")
        valid, invalid = uploader._validate_and_split_data(sample_data)

        # Should have 1 valid record and 2 invalid (anomalies)
        assert len(valid) == 1
        assert len(invalid) == 2

        # Valid record should be the first one (normal temperature/humidity)
        assert valid[0]["temperature"] == 22.5

        # Invalid records should be the anomalies
        invalid_temps = [r["temperature"] for r in invalid]
        assert -50.0 in invalid_temps  # Cold anomaly

        invalid_humidity = [r["humidity"] for r in invalid]
        assert 120.0 in invalid_humidity  # Humidity anomaly

        # Check bucket mapping (SPLIT means goes to both buckets)
        assert uploader.pipeline_bucket_map["validated"] == "SPLIT"

    def test_aggregated_phase_logic(self, sample_data):
        """Test aggregated phase logic."""
        uploader = MockUploader("aggregated")
        valid, invalid = uploader._validate_and_split_data(sample_data)

        assert len(valid) == 3
        assert len(invalid) == 0
        assert uploader.pipeline_bucket_map["aggregated"] == "aggregated"

    def test_anomaly_phase_logic(self, sample_data):
        """Test anomaly phase logic."""
        uploader = MockUploader("anomaly")
        valid, invalid = uploader._validate_and_split_data(sample_data)

        assert len(valid) == 3
        assert len(invalid) == 0
        assert uploader.pipeline_bucket_map["anomaly"] == "anomalies"

    def test_bucket_mappings(self):
        """Test all bucket mappings are correct."""
        uploader = MockUploader()

        expected_mappings = {
            "raw": "ingestion",
            "ingestion": "ingestion",
            "schematized": "schematized",
            "validated": "SPLIT",
            "anomaly": "anomalies",
            "anomalies": "anomalies",
            "aggregated": "aggregated",
            "enriched": "enriched",
            "filtered": "enriched",
        }

        for phase, expected_bucket in expected_mappings.items():
            assert uploader.pipeline_bucket_map[phase] == expected_bucket

    def test_pipeline_switching(self, sample_data):
        """Test switching between pipeline types."""
        uploader = MockUploader("raw")

        # Test raw
        assert uploader.current_pipeline_type == "raw"
        valid, invalid = uploader._validate_and_split_data(sample_data)
        assert len(valid) == 3 and len(invalid) == 0

        # Switch to validated
        uploader.current_pipeline_type = "validated"
        valid, invalid = uploader._validate_and_split_data(sample_data)
        assert len(valid) == 1 and len(invalid) == 2  # Validation splits data

        # Switch to schematized
        uploader.current_pipeline_type = "schematized"
        valid, invalid = uploader._validate_and_split_data(sample_data)
        assert len(valid) == 3 and len(invalid) == 0  # Transform only

    def test_unknown_pipeline_type(self, sample_data):
        """Test handling of unknown pipeline types."""
        uploader = MockUploader("unknown_type")
        valid, invalid = uploader._validate_and_split_data(sample_data)

        # Should default to pass-through behavior
        assert len(valid) == 3
        assert len(invalid) == 0
        assert valid == sample_data

    def test_empty_data(self):
        """Test handling of empty data."""
        uploader = MockUploader("validated")
        valid, invalid = uploader._validate_and_split_data([])

        assert len(valid) == 0
        assert len(invalid) == 0

    @pytest.mark.parametrize("phase,expected_bucket", [
        ("raw", "ingestion"),
        ("schematized", "schematized"),
        ("validated", "SPLIT"),
        ("aggregated", "aggregated"),
        ("anomaly", "anomalies"),
    ])
    def test_phase_bucket_mapping(self, phase, expected_bucket):
        """Test individual phase to bucket mappings."""
        uploader = MockUploader(phase)
        assert uploader.pipeline_bucket_map[phase] == expected_bucket


if __name__ == "__main__":
    # Run tests directly
    import subprocess
    result = subprocess.run([
        "python", "-m", "pytest", __file__, "-v", "--tb=short"
    ], cwd=Path(__file__).parent.parent)
    exit(result.returncode)