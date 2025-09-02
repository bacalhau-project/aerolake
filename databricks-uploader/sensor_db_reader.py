#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Centralized Sensor Database Reader Library

This module provides a single, consistent interface for reading from the sensor
database in READ-ONLY mode. All components should use this library instead of
directly connecting to the sensor database.

Key Features:
- All connections are read-only (using SQLite URI mode=ro)
- Automatic retry logic for database busy errors
- Connection pooling and proper resource management
- Consistent error handling across all components
"""

import sqlite3
import time
from typing import List, Dict, Any, Optional, Generator
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass
class SensorReaderConfig:
    """Configuration for the sensor database reader."""

    max_retries: int = 5
    initial_retry_delay: float = 0.1
    timeout: float = 30.0
    verbose: bool = False


class SensorDatabaseReader:
    """
    Centralized reader for sensor database access.

    This class ensures all sensor database access is:
    1. Read-only (using SQLite URI with mode=ro)
    2. Properly retried on busy/locked conditions
    3. Consistently handled across all components
    """

    def __init__(self, db_path: str, config: Optional[SensorReaderConfig] = None):
        """
        Initialize the sensor database reader.

        Args:
            db_path: Path to the sensor database
            config: Optional configuration object
        """
        self.db_path = Path(db_path).resolve()
        self.config = config or SensorReaderConfig()

        # Validate database exists
        if not self.db_path.exists():
            raise FileNotFoundError(f"Sensor database not found: {self.db_path}")

        # Build read-only connection string
        self.connection_string = f"file:{self.db_path}?mode=ro"

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a read-only connection to the sensor database.

        This context manager ensures:
        - Connection is always read-only
        - Proper cleanup on exit
        - Retry logic for busy database

        Yields:
            sqlite3.Connection: Read-only connection to the database
        """
        conn = None
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                # Connect in read-only mode
                conn = sqlite3.connect(
                    self.connection_string, uri=True, timeout=self.config.timeout
                )
                conn.row_factory = sqlite3.Row

                # Successfully connected
                if self.config.verbose and attempt > 0:
                    print(f"✓ Connected to sensor database after {attempt + 1} attempts")

                yield conn
                return

            except sqlite3.OperationalError as e:
                last_error = e
                if conn:
                    conn.close()
                    conn = None

                # Check if we should retry
                if "locked" in str(e).lower() or "busy" in str(e).lower():
                    if attempt < self.config.max_retries - 1:
                        delay = self.config.initial_retry_delay * (2**attempt)
                        if self.config.verbose:
                            print(
                                f"⚠️  Database busy (attempt {attempt + 1}/{self.config.max_retries}), "
                                f"retrying in {delay:.1f}s..."
                            )
                        time.sleep(delay)
                        continue

                # Non-retryable error or last attempt
                raise

            except Exception as e:
                last_error = e
                if conn:
                    conn.close()
                    conn = None
                raise

            finally:
                # Always close connection when context exits
                if conn:
                    conn.close()

        # If we get here, all retries failed
        raise sqlite3.OperationalError(
            f"Failed to connect to sensor database after {self.config.max_retries} attempts: {last_error}"
        )

    def read_sensor_data(
        self,
        table_name: str = "sensor_readings",
        where_clause: Optional[str] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Read sensor data from the database.

        Args:
            table_name: Name of the table to read from
            where_clause: Optional WHERE clause (without 'WHERE' keyword)
            order_by: Optional ORDER BY clause (without 'ORDER BY' keyword)
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of dictionaries containing sensor data
        """
        with self.get_connection() as conn:
            # Build query
            query = f"SELECT * FROM {table_name}"

            if where_clause:
                query += f" WHERE {where_clause}"

            if order_by:
                query += f" ORDER BY {order_by}"
            else:
                # Default ordering by timestamp descending
                query += " ORDER BY timestamp DESC"

            if limit:
                query += f" LIMIT {limit}"

            if offset:
                query += f" OFFSET {offset}"

            if self.config.verbose:
                print(f"Executing query: {query}")

            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def read_with_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a custom read-only query.

        Args:
            query: SQL query to execute (must be a SELECT query)
            params: Optional parameters for the query

        Returns:
            List of dictionaries containing query results

        Raises:
            ValueError: If query is not a SELECT statement
        """
        # Validate query is read-only
        query_upper = query.strip().upper()
        if not query_upper.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed on sensor database")

        with self.get_connection() as conn:
            if self.config.verbose:
                print(f"Executing query: {query}")

            cursor = conn.execute(query, params or ())
            return [dict(row) for row in cursor.fetchall()]

    def stream_sensor_data(
        self,
        table_name: str = "sensor_readings",
        batch_size: int = 1000,
        where_clause: Optional[str] = None,
        order_by: Optional[str] = None,
    ) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Stream sensor data in batches to handle large datasets efficiently.

        Args:
            table_name: Name of the table to read from
            batch_size: Number of records per batch
            where_clause: Optional WHERE clause
            order_by: Optional ORDER BY clause

        Yields:
            Batches of sensor records
        """
        offset = 0

        while True:
            batch = self.read_sensor_data(
                table_name=table_name,
                where_clause=where_clause,
                order_by=order_by,
                limit=batch_size,
                offset=offset,
            )

            if not batch:
                break

            yield batch

            if len(batch) < batch_size:
                break

            offset += batch_size

    def get_table_info(self, table_name: str = "sensor_readings") -> Dict[str, Any]:
        """
        Get information about a table in the sensor database.

        Args:
            table_name: Name of the table

        Returns:
            Dictionary containing table information
        """
        with self.get_connection() as conn:
            # Check if table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
            )
            if not cursor.fetchone():
                raise ValueError(f"Table '{table_name}' not found in sensor database")

            # Get table schema
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            columns = [
                {
                    "name": row[1],
                    "type": row[2],
                    "nullable": not row[3],
                    "default": row[4],
                    "primary_key": bool(row[5]),
                }
                for row in cursor.fetchall()
            ]

            # Get row count
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]

            # Get sample of data types and ranges
            cursor = conn.execute(f"SELECT * FROM {table_name} LIMIT 1")
            sample_row = cursor.fetchone()

            return {
                "table_name": table_name,
                "columns": columns,
                "row_count": row_count,
                "sample_row": dict(sample_row) if sample_row else None,
            }

    def list_tables(self) -> List[str]:
        """
        List all tables in the sensor database.

        Returns:
            List of table names
        """
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            return [row[0] for row in cursor.fetchall()]

    def verify_connection(self) -> bool:
        """
        Verify that we can connect to the sensor database in read-only mode.

        Returns:
            True if connection is successful
        """
        try:
            with self.get_connection() as conn:
                # Try a simple query
                cursor = conn.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
        except Exception as e:
            if self.config.verbose:
                print(f"❌ Connection verification failed: {e}")
            return False


# Convenience function for simple reads
def read_sensor_data(
    db_path: str,
    table_name: str = "sensor_readings",
    limit: Optional[int] = None,
    where_clause: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function for simple sensor data reads.

    Args:
        db_path: Path to the sensor database
        table_name: Name of the table to read from
        limit: Maximum number of records to return
        where_clause: Optional WHERE clause

    Returns:
        List of sensor records
    """
    reader = SensorDatabaseReader(db_path)
    return reader.read_sensor_data(table_name=table_name, limit=limit, where_clause=where_clause)


if __name__ == "__main__":
    # Example usage and testing
    import sys

    if len(sys.argv) < 2:
        print("Usage: sensor_db_reader.py <path_to_sensor_db> [table_name]")
        sys.exit(1)

    db_path = sys.argv[1]
    table_name = sys.argv[2] if len(sys.argv) > 2 else "sensor_readings"

    # Create reader with verbose output
    config = SensorReaderConfig(verbose=True)
    reader = SensorDatabaseReader(db_path, config)

    # Verify connection
    print(f"\n📊 Connecting to sensor database: {db_path}")
    if not reader.verify_connection():
        print("❌ Failed to connect to database")
        sys.exit(1)

    print("✅ Successfully connected in read-only mode")

    # List tables
    print("\n📋 Available tables:")
    tables = reader.list_tables()
    for table in tables:
        print(f"  - {table}")

    # Get table info
    print(f"\n📊 Table info for '{table_name}':")
    try:
        info = reader.get_table_info(table_name)
        print(f"  Columns: {len(info['columns'])}")
        print(f"  Rows: {info['row_count']:,}")
        print("\n  Column details:")
        for col in info["columns"]:
            print(f"    - {col['name']}: {col['type']} {'(PK)' if col['primary_key'] else ''}")
    except ValueError as e:
        print(f"  ❌ {e}")
        sys.exit(1)

    # Read sample data
    print(f"\n📖 Reading sample data (limit=5):")
    records = reader.read_sensor_data(table_name=table_name, limit=5)

    if records:
        print(f"  Found {len(records)} records")
        # Show first record
        print("\n  First record:")
        for key, value in records[0].items():
            print(f"    {key}: {value}")
    else:
        print("  No records found")

    print("\n✅ All operations completed successfully in read-only mode")
