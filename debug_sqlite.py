#!/usr/bin/env python3
"""Debug SQLite database access"""

import sqlite3
import sys
import os
import traceback


def test_sqlite_support():
    """Test basic SQLite support"""
    print("=== Testing Python SQLite Support ===")
    try:
        import sqlite3

        print("✓ sqlite3 module imported successfully")
        print(f"SQLite version: {sqlite3.sqlite_version}")
        print(f"Python sqlite3 module version: {sqlite3.version}")
        return True
    except Exception as e:
        print(f"✗ Failed to import sqlite3: {e}")
        return False


def test_database_access(db_path):
    """Test database access"""
    print(f"\n=== Testing Database Access: {db_path} ===")

    if not os.path.exists(db_path):
        print(f"Database does not exist: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        print("✓ Database connection successful")

        # List tables
        cursor = conn.execute('SELECT name FROM sqlite_master WHERE type="table"')
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables found: {tables}")

        # Check pipeline_config table
        if "pipeline_config" in tables:
            cursor = conn.execute("SELECT COUNT(*) FROM pipeline_config")
            count = cursor.fetchone()[0]
            print(f"Records in pipeline_config: {count}")

            if count > 0:
                cursor = conn.execute(
                    "SELECT pipeline_type, created_at, is_active FROM pipeline_config ORDER BY created_at DESC LIMIT 3"
                )
                records = cursor.fetchall()
                print("Recent records:")
                for record in records:
                    print(f"  {record}")
        else:
            print("No pipeline_config table found")

        conn.close()
        return True

    except Exception as e:
        print(f"✗ Failed to access database: {e}")
        print(f"Exception type: {type(e).__name__}")
        traceback.print_exc()
        return False


def main():
    print("Database Debug Script")
    print("====================")

    # Test SQLite support
    if not test_sqlite_support():
        sys.exit(1)

    # Test both database locations
    db_paths = ["/bacalhau_data/state/pipeline_config.db", "/bacalhau_data/pipeline_config.db"]

    for db_path in db_paths:
        test_database_access(db_path)


if __name__ == "__main__":
    main()
