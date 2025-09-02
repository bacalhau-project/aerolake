#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

import sqlite3
import os
import sys


def check_pipeline_state():
    state_dir = os.environ.get("STATE_DIR", "/bacalhau_data/state")
    db_path = os.path.join(state_dir, "pipeline_config.db")

    print(f"🔍 Checking pipeline state database: {db_path}")

    if not os.path.exists(db_path):
        print(f"❌ Database file does not exist: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get current pipeline type
        cursor.execute("SELECT key, value FROM config WHERE key = 'current_pipeline_type'")
        result = cursor.fetchone()

        if result:
            print(f"✅ Current pipeline type: {result[1]}")
        else:
            print("❌ No pipeline type found in database")

        # Show all config entries
        cursor.execute("SELECT key, value FROM config")
        all_config = cursor.fetchall()

        print("\n📋 All configuration entries:")
        for key, value in all_config:
            print(f"   {key}: {value}")

        conn.close()

    except Exception as e:
        print(f"❌ Error reading database: {e}")


if __name__ == "__main__":
    check_pipeline_state()
