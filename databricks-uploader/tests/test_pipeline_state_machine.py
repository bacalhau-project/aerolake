#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pytest>=7.0",
#   "pytest-mock",
#   "pyyaml>=6.0",
#   "boto3>=1.26.0",
# ]
# ///

"""
Pipeline State Machine Unit Tests

Tests the pipeline configuration management and state transitions:
1. Pipeline type persistence in SQLite
2. Configuration retrieval and fallback logic
3. Pipeline switching and history tracking
4. State machine behavior validation
"""

import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch
import pytest
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from pipeline_manager import PipelineManager


class TestPipelineStateMachine:
    """Test pipeline state management and configuration logic."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            yield f.name
            Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def pipeline_manager(self, temp_db):
        """Create pipeline manager with temporary database."""
        return PipelineManager(temp_db)

    def test_initial_state_default(self, pipeline_manager):
        """Test initial state when no configuration exists."""
        config = pipeline_manager.get_current_config()

        assert config["type"] == "raw"  # Default fallback
        assert config["source"] == "default"
        assert "created_at" in config

    def test_initial_state_from_environment(self, temp_db):
        """Test initial state when PIPELINE_TYPE environment variable is set."""
        with patch.dict('os.environ', {'PIPELINE_TYPE': 'validated'}):
            manager = PipelineManager(temp_db)
            config = manager.get_current_config()

            assert config["type"] == "validated"
            assert config["source"] == "environment"

    def test_set_pipeline_type(self, pipeline_manager):
        """Test setting pipeline type and persistence."""
        # Set to schematized
        pipeline_manager.set_pipeline_type("schematized", "test_user")

        config = pipeline_manager.get_current_config()
        assert config["type"] == "schematized"
        assert config["source"] == "test_user"  # created_by becomes source

    def test_pipeline_type_persistence_across_instances(self, temp_db):
        """Test that pipeline type persists across manager instances."""
        # Set pipeline type in first instance
        manager1 = PipelineManager(temp_db)
        manager1.set_pipeline_type("validated", "user1")

        # Create new instance and verify persistence
        manager2 = PipelineManager(temp_db)
        config = manager2.get_current_config()

        assert config["type"] == "validated"
        assert config["source"] == "user1"

    def test_pipeline_type_switching(self, pipeline_manager):
        """Test switching between pipeline types."""
        # Set initial type
        pipeline_manager.set_pipeline_type("raw", "user1")
        config1 = pipeline_manager.get_current_config()
        assert config1["type"] == "raw"

        # Switch to different type
        pipeline_manager.set_pipeline_type("validated", "user2")
        config2 = pipeline_manager.get_current_config()
        assert config2["type"] == "validated"
        assert config2["source"] == "user2"

        # Switch again
        pipeline_manager.set_pipeline_type("schematized", "user3")
        config3 = pipeline_manager.get_current_config()
        assert config3["type"] == "schematized"
        assert config3["source"] == "user3"

    def test_execution_recording(self, pipeline_manager):
        """Test recording pipeline executions."""
        # Record execution
        s3_locations = ["s3://bucket1/file1.json", "s3://bucket2/file2.json"]
        pipeline_manager.record_execution(
            pipeline_type="validated",
            records_processed=150,
            s3_locations=s3_locations,
            job_id="job_123"
        )

        # Get execution history
        history = pipeline_manager.get_execution_history()

        assert len(history) == 1
        execution = history[0]
        assert execution["pipeline_type"] == "validated"
        assert execution["records_processed"] == 150
        assert execution["s3_locations"] == s3_locations
        assert execution["job_id"] == "job_123"

    def test_execution_history_ordering(self, pipeline_manager):
        """Test that execution history is ordered by most recent first."""
        # Record multiple executions
        executions = [
            ("raw", 50, ["s3://bucket/file1.json"], "job_1"),
            ("validated", 75, ["s3://bucket/file2.json"], "job_2"),
            ("schematized", 100, ["s3://bucket/file3.json"], "job_3")
        ]

        for pipeline_type, records, locations, job_id in executions:
            pipeline_manager.record_execution(pipeline_type, records, locations, job_id)

        history = pipeline_manager.get_execution_history()

        # Should be ordered most recent first
        assert len(history) == 3
        assert history[0]["job_id"] == "job_3"  # Most recent
        assert history[1]["job_id"] == "job_2"
        assert history[2]["job_id"] == "job_1"  # Oldest

    def test_valid_pipeline_types(self, pipeline_manager):
        """Test setting various valid pipeline types."""
        valid_types = ["raw", "validated", "schematized", "aggregated", "anomaly", "enriched"]

        for pipeline_type in valid_types:
            pipeline_manager.set_pipeline_type(pipeline_type, "test_user")
            config = pipeline_manager.get_current_config()
            assert config["type"] == pipeline_type

    def test_database_schema_creation(self, temp_db):
        """Test that database tables are created correctly."""
        manager = PipelineManager(temp_db)

        # Check that tables exist and have correct structure
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Check pipeline_config table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pipeline_config'")
        assert cursor.fetchone() is not None

        cursor.execute("PRAGMA table_info(pipeline_config)")
        columns = [col[1] for col in cursor.fetchall()]
        expected_columns = ["id", "pipeline_type", "created_at", "created_by", "is_active"]
        for col in expected_columns:
            assert col in columns

        # Check pipeline_executions table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pipeline_executions'")
        assert cursor.fetchone() is not None

        cursor.execute("PRAGMA table_info(pipeline_executions)")
        columns = [col[1] for col in cursor.fetchall()]
        expected_columns = ["id", "pipeline_type", "records_processed", "s3_locations", "job_id", "created_at"]
        for col in expected_columns:
            assert col in columns

        conn.close()

    def test_config_source_priority(self, temp_db):
        """Test configuration source priority: database > environment > default."""
        # Test 1: Database overrides environment
        with patch.dict('os.environ', {'PIPELINE_TYPE': 'raw'}):
            manager = PipelineManager(temp_db)

            # Set in database
            manager.set_pipeline_type("validated", "db_user")

            # Should use database value, not environment
            config = manager.get_current_config()
            assert config["type"] == "validated"
            assert config["source"] == "db_user"

        # Test 2: Environment overrides default (when no database config)
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            clean_db = f.name
        try:
            with patch.dict('os.environ', {'PIPELINE_TYPE': 'schematized'}):
                manager2 = PipelineManager(clean_db)
                config = manager2.get_current_config()
                assert config["type"] == "schematized"
                assert config["source"] == "environment"
        finally:
            Path(clean_db).unlink(missing_ok=True)

    def test_execution_history_limit(self, pipeline_manager):
        """Test execution history retrieval with limits."""
        # Record many executions
        for i in range(15):
            pipeline_manager.record_execution(
                pipeline_type="raw",
                records_processed=i * 10,
                s3_locations=[f"s3://bucket/file{i}.json"],
                job_id=f"job_{i:02d}"
            )

        # Get limited history
        history = pipeline_manager.get_execution_history(limit=5)
        assert len(history) == 5

        # Should be most recent first
        assert history[0]["job_id"] == "job_14"
        assert history[4]["job_id"] == "job_10"

    def test_concurrent_access_safety(self, temp_db):
        """Test basic concurrent access scenarios."""
        # Create two managers pointing to same database
        manager1 = PipelineManager(temp_db)
        manager2 = PipelineManager(temp_db)

        # Manager 1 sets type
        manager1.set_pipeline_type("validated", "user1")

        # Manager 2 should see the change
        config = manager2.get_current_config()
        assert config["type"] == "validated"
        assert config["source"] == "user1"

        # Manager 2 updates
        manager2.set_pipeline_type("schematized", "user2")

        # Manager 1 should see the new change
        config = manager1.get_current_config()
        assert config["type"] == "schematized"
        assert config["source"] == "user2"

    def test_malformed_data_handling(self, pipeline_manager):
        """Test handling of edge cases and malformed data."""
        # Test with empty job ID
        pipeline_manager.record_execution(
            pipeline_type="raw",
            records_processed=0,
            s3_locations=[],
            job_id=""
        )

        history = pipeline_manager.get_execution_history()
        assert len(history) == 1
        assert history[0]["job_id"] == ""
        assert history[0]["records_processed"] == 0
        assert history[0]["s3_locations"] == []


if __name__ == "__main__":
    # Run tests directly
    import subprocess
    result = subprocess.run([
        "python", "-m", "pytest", __file__, "-v", "--tb=short"
    ], cwd=Path(__file__).parent.parent)
    exit(result.returncode)