#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pytest>=7.0",
#   "pytest-mock",
# ]
# ///

"""
Test suite for the centralized sensor database reader.

Tests the SensorDatabaseReader class to ensure:
1. All connections are read-only
2. Retry logic works correctly
3. Error handling is proper
4. Query building is correct
"""

import sqlite3
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from sensor_db_reader import SensorDatabaseReader, SensorReaderConfig


class TestSensorDatabaseReader:
    """Test cases for SensorDatabaseReader"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary SQLite database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        # Create test table and data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE sensor_readings (
                id INTEGER PRIMARY KEY,
                turbine_id TEXT,
                timestamp TEXT,
                sensor_type TEXT,
                value REAL,
                farm_id TEXT
            )
        """)

        # Insert test data
        test_data = [
            ("T001", "2024-01-01T10:00:00", "power", 1500.0, "F001"),
            ("T001", "2024-01-01T10:01:00", "wind_speed", 12.5, "F001"),
            ("T002", "2024-01-01T10:00:00", "temperature", 25.3, "F001"),
            ("T002", "2024-01-01T10:01:00", "vibration", 0.05, "F001"),
            ("T003", "2024-01-01T10:02:00", "rpm", 15.2, "F002"),
        ]

        cursor.executemany(
            "INSERT INTO sensor_readings (turbine_id, timestamp, sensor_type, value, farm_id) VALUES (?, ?, ?, ?, ?)",
            test_data,
        )

        conn.commit()
        conn.close()

        yield db_path

        # Cleanup
        Path(db_path).unlink()

    def test_read_only_connection(self, temp_db):
        """Test that connections are always read-only"""
        reader = SensorDatabaseReader(temp_db)

        with reader.get_connection() as conn:
            # Attempt to write should fail
            with pytest.raises(sqlite3.OperationalError) as exc_info:
                conn.execute("INSERT INTO sensor_readings (turbine_id) VALUES ('T999')")

            assert (
                "read-only" in str(exc_info.value).lower()
                or "readonly" in str(exc_info.value).lower()
            )

    def test_read_sensor_data(self, temp_db):
        """Test reading sensor data"""
        reader = SensorDatabaseReader(temp_db)

        # Read all data
        records = reader.read_sensor_data(table_name="sensor_readings")
        assert len(records) == 5

        # Read with limit
        records = reader.read_sensor_data(table_name="sensor_readings", limit=2)
        assert len(records) == 2

        # Read with where clause
        records = reader.read_sensor_data(
            table_name="sensor_readings", where_clause="turbine_id = 'T001'"
        )
        assert len(records) == 2
        assert all(r["turbine_id"] == "T001" for r in records)

    def test_read_with_query(self, temp_db):
        """Test custom query execution"""
        reader = SensorDatabaseReader(temp_db)

        # Valid SELECT query
        query = "SELECT DISTINCT turbine_id FROM sensor_readings"
        records = reader.read_with_query(query)
        assert len(records) == 3

        # Should reject non-SELECT queries
        with pytest.raises(ValueError) as exc_info:
            reader.read_with_query("UPDATE sensor_readings SET value = 0")
        assert "Only SELECT queries are allowed" in str(exc_info.value)

    def test_stream_sensor_data(self, temp_db):
        """Test streaming data in batches"""
        reader = SensorDatabaseReader(temp_db)

        # Stream with batch size of 2
        batches = list(reader.stream_sensor_data(table_name="sensor_readings", batch_size=2))

        assert len(batches) == 3  # 5 records / 2 per batch = 3 batches
        assert len(batches[0]) == 2
        assert len(batches[1]) == 2
        assert len(batches[2]) == 1  # Last batch has remaining record

    def test_get_table_info(self, temp_db):
        """Test getting table information"""
        reader = SensorDatabaseReader(temp_db)

        info = reader.get_table_info("sensor_readings")

        assert info["table_name"] == "sensor_readings"
        assert info["row_count"] == 5
        assert len(info["columns"]) == 6  # id, turbine_id, timestamp, sensor_type, value, farm_id

        # Check column details
        id_col = next(c for c in info["columns"] if c["name"] == "id")
        assert id_col["primary_key"] is True
        assert id_col["type"] == "INTEGER"

    def test_list_tables(self, temp_db):
        """Test listing all tables"""
        reader = SensorDatabaseReader(temp_db)

        tables = reader.list_tables()
        assert "sensor_readings" in tables

    def test_verify_connection(self, temp_db):
        """Test connection verification"""
        reader = SensorDatabaseReader(temp_db)

        assert reader.verify_connection() is True

        # Test with non-existent database
        bad_reader = SensorDatabaseReader.__new__(SensorDatabaseReader)
        bad_reader.db_path = Path("/nonexistent/database.db")
        bad_reader.connection_string = f"file:{bad_reader.db_path}?mode=ro"
        bad_reader.config = SensorReaderConfig(verbose=False)

        assert bad_reader.verify_connection() is False

    def test_retry_logic(self, temp_db, mocker):
        """Test retry logic for busy database"""
        config = SensorReaderConfig(
            max_retries=3,
            initial_retry_delay=0.01,  # Short delay for testing
            verbose=True,
        )
        reader = SensorDatabaseReader(temp_db, config)

        # Mock sqlite3.connect to fail twice then succeed
        original_connect = sqlite3.connect
        call_count = 0

        def mock_connect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise sqlite3.OperationalError("database is locked")
            return original_connect(*args, **kwargs)

        with patch("sqlite3.connect", side_effect=mock_connect):
            records = reader.read_sensor_data(limit=1)
            assert len(records) == 1
            assert call_count == 3  # Failed twice, succeeded on third try

    def test_database_not_found(self):
        """Test handling of non-existent database"""
        with pytest.raises(FileNotFoundError) as exc_info:
            SensorDatabaseReader("/nonexistent/database.db")
        assert "Sensor database not found" in str(exc_info.value)

    def test_table_not_found(self, temp_db):
        """Test handling of non-existent table"""
        reader = SensorDatabaseReader(temp_db)

        with pytest.raises(ValueError) as exc_info:
            reader.get_table_info("nonexistent_table")
        assert "Table 'nonexistent_table' not found" in str(exc_info.value)

    def test_ordering(self, temp_db):
        """Test ordering of results"""
        reader = SensorDatabaseReader(temp_db)

        # Test ascending order
        records = reader.read_sensor_data(table_name="sensor_readings", order_by="timestamp ASC")
        timestamps = [r["timestamp"] for r in records]
        assert timestamps == sorted(timestamps)

        # Test descending order (default)
        records = reader.read_sensor_data(table_name="sensor_readings")
        timestamps = [r["timestamp"] for r in records]
        assert timestamps == sorted(timestamps, reverse=True)


def test_convenience_function(temp_db):
    """Test the convenience function for simple reads"""
    from sensor_db_reader import read_sensor_data

    records = read_sensor_data(temp_db, table_name="sensor_readings", limit=3)

    assert len(records) == 3
    assert all(isinstance(r, dict) for r in records)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
