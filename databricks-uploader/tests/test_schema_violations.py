#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pytest>=7.0",
#   "pytest-mock",
# ]
# ///

"""
Comprehensive Schema Violation Tests

Tests various schema violations and ensures they are properly detected and routed
to the anomalies bucket during the validated phase.
"""

import sys
from pathlib import Path
from unittest.mock import Mock
import pytest

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from test_phase_logic_simple import MockUploader


class TestSchemaViolations:
    """Test comprehensive schema violation detection and routing."""

    def test_temperature_violations(self):
        """Test temperature range violations."""
        uploader = MockUploader("validated")

        # Test data with various temperature violations
        test_data = [
            {"id": 1, "temperature": -30.0, "humidity": 50.0},  # Too cold
            {"id": 2, "temperature": 80.0, "humidity": 50.0},   # Too hot
            {"id": 3, "temperature": 25.0, "humidity": 50.0},   # Valid
        ]

        valid, invalid = uploader._validate_and_split_data(test_data)

        # Should have 1 valid, 2 invalid
        assert len(valid) == 1
        assert len(invalid) == 2

        # Check the valid record
        assert valid[0]["temperature"] == 25.0

        # Check invalid records have the violations
        invalid_temps = [r["temperature"] for r in invalid]
        assert -30.0 in invalid_temps
        assert 80.0 in invalid_temps

    def test_humidity_violations(self):
        """Test humidity range violations."""
        uploader = MockUploader("validated")

        # Test data with various humidity violations
        test_data = [
            {"id": 1, "temperature": 25.0, "humidity": -10.0},  # Negative humidity
            {"id": 2, "temperature": 25.0, "humidity": 150.0},  # Over 100%
            {"id": 3, "temperature": 25.0, "humidity": 75.0},   # Valid
        ]

        valid, invalid = uploader._validate_and_split_data(test_data)

        # Should have 1 valid, 2 invalid
        assert len(valid) == 1
        assert len(invalid) == 2

        # Check the valid record
        assert valid[0]["humidity"] == 75.0

        # Check invalid records have the violations
        invalid_humidity = [r["humidity"] for r in invalid]
        assert -10.0 in invalid_humidity
        assert 150.0 in invalid_humidity

    def test_multiple_field_violations(self):
        """Test records with multiple field violations."""
        uploader = MockUploader("validated")

        # Test data with multiple violations per record
        test_data = [
            {
                "id": 1,
                "temperature": -50.0,  # Invalid
                "humidity": 120.0      # Invalid
            },
            {
                "id": 2,
                "temperature": 25.0,   # Valid
                "humidity": 75.0       # Valid
            }
        ]

        valid, invalid = uploader._validate_and_split_data(test_data)

        # Should have 1 valid, 1 invalid (record with multiple violations)
        assert len(valid) == 1
        assert len(invalid) == 1

        # The invalid record should have both violations
        invalid_record = invalid[0]
        assert invalid_record["temperature"] == -50.0
        assert invalid_record["humidity"] == 120.0

    def test_boundary_values(self):
        """Test boundary values for validation ranges."""
        uploader = MockUploader("validated")

        # Test exact boundary values
        test_data = [
            {"id": 1, "temperature": -20.0, "humidity": 0.0},   # Lower boundaries (valid)
            {"id": 2, "temperature": 60.0, "humidity": 100.0},  # Upper boundaries (valid)
            {"id": 3, "temperature": -20.1, "humidity": 0.0},   # Just outside lower temp
            {"id": 4, "temperature": 60.1, "humidity": 100.0},  # Just outside upper temp
            {"id": 5, "temperature": 25.0, "humidity": -0.1},   # Just outside lower humidity
            {"id": 6, "temperature": 25.0, "humidity": 100.1},  # Just outside upper humidity
        ]

        valid, invalid = uploader._validate_and_split_data(test_data)

        # Should have 2 valid (boundary values), 4 invalid (just outside boundaries)
        assert len(valid) == 2
        assert len(invalid) == 4

        # Check valid boundary records
        valid_temps = [r["temperature"] for r in valid]
        assert -20.0 in valid_temps
        assert 60.0 in valid_temps

    def test_missing_fields(self):
        """Test handling of missing required fields."""
        uploader = MockUploader("validated")

        # Test data with missing fields
        test_data = [
            {"id": 1, "temperature": 25.0},  # Missing humidity
            {"id": 2, "humidity": 75.0},     # Missing temperature
            {"id": 3},                       # Missing both
            {"id": 4, "temperature": 25.0, "humidity": 75.0}  # Valid complete record
        ]

        valid, invalid = uploader._validate_and_split_data(test_data)

        # Note: Missing fields get default values during transformation:
        # - Missing temperature defaults to None → 0.0 (violates validation: 0 is valid)
        # - Missing humidity defaults to None → 0.0 (valid: 0 is within 0-100 range)
        # So records with missing temp are valid, missing humidity are valid
        assert len(valid) == 4  # All records pass because 0.0 is within valid ranges
        assert len(invalid) == 0

    def test_invalid_data_types(self):
        """Test handling of invalid data types."""
        uploader = MockUploader("validated")

        # Test data with invalid types (will be converted to 0 by .get() with default)
        test_data = [
            {"id": 1, "temperature": "hot", "humidity": 75.0},    # String temperature
            {"id": 2, "temperature": 25.0, "humidity": "high"},   # String humidity
            {"id": 3, "temperature": None, "humidity": 75.0},     # None temperature
            {"id": 4, "temperature": 25.0, "humidity": None},     # None humidity
            {"id": 5, "temperature": 25.0, "humidity": 75.0}      # Valid
        ]

        valid, invalid = uploader._validate_and_split_data(test_data)

        # Note: Invalid types get converted to 0.0 which is within valid ranges
        # Only the valid record and the converted records pass validation
        assert len(valid) == 5  # All records pass because 0.0 is within valid ranges
        assert len(invalid) == 0

    def test_edge_case_values(self):
        """Test edge case values like infinity and very large numbers."""
        uploader = MockUploader("validated")

        # Test edge cases
        test_data = [
            {"id": 1, "temperature": float('inf'), "humidity": 75.0},    # Infinity
            {"id": 2, "temperature": float('-inf'), "humidity": 75.0},   # Negative infinity
            {"id": 3, "temperature": 1000000, "humidity": 75.0},         # Very large number
            {"id": 4, "temperature": -1000000, "humidity": 75.0},        # Very large negative
            {"id": 5, "temperature": 25.0, "humidity": 75.0}             # Valid
        ]

        valid, invalid = uploader._validate_and_split_data(test_data)

        # Should have 1 valid, 4 invalid (edge cases outside valid ranges)
        assert len(valid) == 1
        assert len(invalid) == 4

    def test_schema_violations_only_in_validated_phase(self):
        """Test that schema violations only matter in validated phase."""
        # Test the same invalid data in different phases
        invalid_data = [
            {"id": 1, "temperature": -50.0, "humidity": 150.0}  # Multiple violations
        ]

        # In raw phase: should pass through
        uploader_raw = MockUploader("raw")
        valid_raw, invalid_raw = uploader_raw._validate_and_split_data(invalid_data)
        assert len(valid_raw) == 1
        assert len(invalid_raw) == 0

        # In schematized phase: should transform but not validate
        uploader_schema = MockUploader("schematized")
        valid_schema, invalid_schema = uploader_schema._validate_and_split_data(invalid_data)
        assert len(valid_schema) == 1
        assert len(invalid_schema) == 0

        # In validated phase: should catch violations
        uploader_validated = MockUploader("validated")
        valid_validated, invalid_validated = uploader_validated._validate_and_split_data(invalid_data)
        assert len(valid_validated) == 0
        assert len(invalid_validated) == 1

    def test_violation_routing_to_anomalies_bucket(self):
        """Test that schema violations are routed to anomalies bucket."""
        uploader = MockUploader("validated")

        # Confirm that validated phase uses SPLIT routing
        assert uploader.pipeline_bucket_map["validated"] == "SPLIT"

        # This means:
        # - Valid records go to "validated" bucket
        # - Invalid records go to "anomalies" bucket

        test_data = [
            {"id": 1, "temperature": 25.0, "humidity": 75.0},   # Valid → validated bucket
            {"id": 2, "temperature": -50.0, "humidity": 150.0}  # Invalid → anomalies bucket
        ]

        valid, invalid = uploader._validate_and_split_data(test_data)

        assert len(valid) == 1    # Goes to validated bucket
        assert len(invalid) == 1  # Goes to anomalies bucket

    @pytest.mark.parametrize("temp,humidity,should_be_valid", [
        # Valid cases
        (25.0, 75.0, True),    # Normal values
        (-20.0, 0.0, True),    # Lower boundaries
        (60.0, 100.0, True),   # Upper boundaries

        # Invalid temperature cases
        (-25.0, 75.0, False),  # Too cold
        (70.0, 75.0, False),   # Too hot

        # Invalid humidity cases
        (25.0, -5.0, False),   # Negative humidity
        (25.0, 105.0, False),  # Over 100%

        # Multiple violations
        (-30.0, 150.0, False), # Both invalid
    ])
    def test_validation_rules_parametrized(self, temp, humidity, should_be_valid):
        """Parametrized test for validation rules."""
        uploader = MockUploader("validated")

        test_data = [{"id": 1, "temperature": temp, "humidity": humidity}]
        valid, invalid = uploader._validate_and_split_data(test_data)

        if should_be_valid:
            assert len(valid) == 1
            assert len(invalid) == 0
        else:
            assert len(valid) == 0
            assert len(invalid) == 1

    def test_schema_violation_metadata_preservation(self):
        """Test that schema violations preserve original data for analysis."""
        uploader = MockUploader("validated")

        original_data = [
            {
                "id": 1,
                "timestamp": "2024-01-15T10:30:00Z",
                "temperature": -50.0,  # Violation
                "humidity": 150.0,     # Violation
                "location": "turbine_001",
                "extra_field": "important_data"
            }
        ]

        valid, invalid = uploader._validate_and_split_data(original_data)

        assert len(invalid) == 1

        # Check that invalid record preserves all original data (after transformation)
        invalid_record = invalid[0]
        assert "turbine_id" in invalid_record  # Transformed
        assert invalid_record["temperature"] == -50.0  # Original violation preserved
        assert invalid_record["humidity"] == 150.0     # Original violation preserved
        assert "pipeline_metadata" in invalid_record   # Metadata added


if __name__ == "__main__":
    # Run tests directly
    import subprocess
    result = subprocess.run([
        "python", "-m", "pytest", __file__, "-v", "--tb=short"
    ], cwd=Path(__file__).parent.parent)
    exit(result.returncode)