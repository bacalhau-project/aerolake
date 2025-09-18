#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "rich",
# ]
# ///

"""
Pipeline configuration controller that manages pipeline state in a SEPARATE database.
This ensures the sensor database remains read-only for all tools.
"""

import sqlite3
import argparse
import time
from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List
from rich.console import Console
from rich.table import Table
from rich.live import Live
from sensor_db_reader import SensorDatabaseReader, SensorReaderConfig


class PipelineType(Enum):
    """Pipeline type enumeration - matches databricks-uploader supported types."""

    # Primary pipeline types
    RAW = "raw"
    INGESTION = "ingestion"
    VALIDATED = "validated"
    SCHEMATIZED = "schematized"
    ENRICHED = "enriched"
    FILTERED = "filtered"
    AGGREGATED = "aggregated"
    ANOMALY = "anomaly"
    ANOMALIES = "anomalies"


class PipelineController:
    """
    Controller for managing pipeline configuration in a separate database.

    IMPORTANT: This controller uses a separate configuration database
    (pipeline_config.db) instead of writing to the sensor database.
    This ensures the sensor database remains read-only for all tools.
    """

    def __init__(self, config_db_path: str = None):
        """
        Initialize the pipeline controller.

        Args:
            config_db_path: Path to the configuration database (NOT the sensor database)
                          Defaults to 'pipeline_config.db' in the current directory
        """
        if config_db_path is None:
            config_db_path = "pipeline_config.db"

        # Ensure we're not accidentally using the sensor database
        if "sensor_data" in str(config_db_path).lower():
            raise ValueError(
                "Pipeline configuration should use a separate database, "
                "not the sensor database. Use 'pipeline_config.db' instead."
            )

        self.config_db_path = Path(config_db_path)
        self.console = Console()
        self._init_database()

    def _init_database(self):
        """Initialize the pipeline configuration table if it doesn't exist."""
        with sqlite3.connect(self.config_db_path, timeout=30.0) as conn:
            conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better concurrency

            # Create table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_config (
                    id INTEGER PRIMARY KEY,
                    pipeline_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    created_by TEXT,
                    reason TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Check and add missing columns for backward compatibility
            cursor = conn.execute("PRAGMA table_info(pipeline_config)")
            columns = {row[1] for row in cursor.fetchall()}

            # Add missing columns if they don't exist
            if "created_by" not in columns:
                conn.execute("ALTER TABLE pipeline_config ADD COLUMN created_by TEXT")
                self.console.print("[yellow]Added missing column: created_by[/yellow]")

            if "reason" not in columns:
                conn.execute("ALTER TABLE pipeline_config ADD COLUMN reason TEXT")
                self.console.print("[yellow]Added missing column: reason[/yellow]")

            if "is_active" not in columns:
                conn.execute("ALTER TABLE pipeline_config ADD COLUMN is_active INTEGER DEFAULT 1")
                # Set all existing records to active since we didn't have this field before
                conn.execute("UPDATE pipeline_config SET is_active = 1 WHERE is_active IS NULL")
                self.console.print("[yellow]Added missing column: is_active[/yellow]")

            # Create index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_pipeline_config_created_at 
                ON pipeline_config(created_at DESC)
            """)

            # Check if there's any configuration
            cursor = conn.execute("SELECT COUNT(*) FROM pipeline_config WHERE is_active = 1")
            if cursor.fetchone()[0] == 0:
                # Insert default configuration
                conn.execute(
                    """
                    INSERT INTO pipeline_config (pipeline_type, created_at, created_by, reason, is_active)
                    VALUES (?, datetime('now'), ?, ?, 1)
                """,
                    (PipelineType.RAW.value, "system", "Initial configuration"),
                )

            conn.commit()

    def get_current_pipeline(self) -> dict:
        """Get the current pipeline configuration atomically."""
        max_retries = 5
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                with sqlite3.connect(self.config_db_path, timeout=30.0) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute("""
                        SELECT pipeline_type, created_at, created_by, reason
                        FROM pipeline_config
                        WHERE is_active = 1
                        ORDER BY id DESC
                        LIMIT 1
                    """)

                    row = cursor.fetchone()
                    if row:
                        return dict(row)
                    else:
                        return {
                            "pipeline_type": PipelineType.RAW.value,
                            "created_at": datetime.now().isoformat(),
                            "created_by": "system",
                            "reason": "Default configuration",
                        }

            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(retry_delay * (2**attempt))  # Exponential backoff
                    continue
                raise

        raise RuntimeError("Failed to read pipeline configuration after multiple attempts")

    def set_pipeline(
        self, pipeline_type: PipelineType, created_by: str = None, reason: str = None
    ) -> bool:
        """
        Set the pipeline configuration atomically.

        Args:
            pipeline_type: The pipeline type to set
            created_by: Who is making this change
            reason: Reason for the change

        Returns:
            True if successful, False otherwise
        """
        max_retries = 5
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                with sqlite3.connect(self.config_db_path, timeout=30.0) as conn:
                    # Use IMMEDIATE transaction to acquire write lock immediately
                    conn.execute("BEGIN IMMEDIATE")

                    try:
                        # Deactivate current configuration
                        conn.execute("UPDATE pipeline_config SET is_active = 0 WHERE is_active = 1")

                        # Insert new configuration
                        conn.execute(
                            """
                            INSERT INTO pipeline_config (pipeline_type, created_at, created_by, reason, is_active)
                            VALUES (?, datetime('now'), ?, ?, 1)
                        """,
                            (pipeline_type.value, created_by or "unknown", reason),
                        )

                        conn.commit()
                        return True

                    except Exception:
                        conn.rollback()
                        raise

            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(retry_delay * (2**attempt))  # Exponential backoff
                    continue
                raise

        return False

    def get_history(self, limit: int = 10) -> List[Dict]:
        """Get the history of pipeline configuration changes."""
        with sqlite3.connect(self.config_db_path, timeout=30.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT pipeline_type, created_at, created_by, reason, is_active
                FROM pipeline_config
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (limit,),
            )

            return [dict(row) for row in cursor.fetchall()]

    def monitor_changes(self, interval: int = 2):
        """Monitor pipeline configuration changes in real-time."""
        last_config = self.get_current_pipeline()

        with Live(self._create_status_table(last_config), refresh_per_second=1) as live:
            while True:
                try:
                    current_config = self.get_current_pipeline()

                    if current_config != last_config:
                        self.console.print(
                            f"\n[yellow]⚠️  Pipeline changed from {last_config['pipeline_type']} "
                            f"to {current_config['pipeline_type']}[/yellow]"
                        )
                        if current_config.get("reason"):
                            self.console.print(f"   Reason: {current_config['reason']}")
                        last_config = current_config

                    live.update(self._create_status_table(current_config))
                    time.sleep(interval)

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.console.print(f"[red]Error: {e}[/red]")
                    time.sleep(interval)

    def _create_status_table(self, config: dict) -> Table:
        """Create a status table for display."""
        table = Table(title="Pipeline Configuration Monitor")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Pipeline Type", config["pipeline_type"])
        table.add_row("Last Updated", config["created_at"])
        table.add_row("Updated By", config.get("created_by", "unknown"))
        if config.get("reason"):
            table.add_row("Reason", config["reason"])
        table.add_row("Config Database", str(self.config_db_path))

        return table

    def read_sensor_data(self, sensor_db_path: str, limit: int = 10) -> List[Dict]:
        """
        Read sensor data from the sensor database using centralized reader.

        Args:
            sensor_db_path: Path to the sensor database
            limit: Number of records to read

        Returns:
            List of sensor records
        """
        # Use centralized sensor reader
        config = SensorReaderConfig(verbose=False)
        reader = SensorDatabaseReader(sensor_db_path, config)

        return reader.read_sensor_data(
            table_name="sensor_readings", order_by="timestamp DESC", limit=limit
        )


def main():
    parser = argparse.ArgumentParser(description="Pipeline Configuration Controller")
    parser.add_argument(
        "--config-db",
        default="pipeline_config.db",
        help="Path to configuration database (NOT the sensor database)",
    )
    parser.add_argument("--sensor-db", help="Path to sensor database (for read-only operations)")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Get current pipeline
    subparsers.add_parser("get", help="Get current pipeline configuration")

    # Set pipeline
    set_parser = subparsers.add_parser("set", help="Set pipeline configuration")
    set_parser.add_argument(
        "pipeline_type", choices=[pt.value for pt in PipelineType], help="Pipeline type to set"
    )
    set_parser.add_argument("--by", help="Who is making this change")
    set_parser.add_argument("--reason", help="Reason for the change")

    # Get history
    history_parser = subparsers.add_parser("history", help="View configuration history")
    history_parser.add_argument("--limit", type=int, default=10, help="Number of records to show")

    # Monitor changes
    monitor_parser = subparsers.add_parser("monitor", help="Monitor configuration changes")
    monitor_parser.add_argument("--interval", type=int, default=2, help="Check interval in seconds")

    # Read sensor data (read-only)
    sensor_parser = subparsers.add_parser("read-sensor", help="Read sensor data (read-only)")
    sensor_parser.add_argument("--limit", type=int, default=10, help="Number of records to read")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        controller = PipelineController(args.config_db)
        console = Console()

        if args.command == "get":
            config = controller.get_current_pipeline()
            table = Table(title="Current Pipeline Configuration")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Pipeline Type", config["pipeline_type"])
            table.add_row("Last Updated", config["created_at"])
            table.add_row("Updated By", config.get("created_by", "unknown"))
            if config.get("reason"):
                table.add_row("Reason", config["reason"])

            console.print(table)

        elif args.command == "set":
            pipeline_type = PipelineType(args.pipeline_type)
            success = controller.set_pipeline(pipeline_type, args.by, args.reason)

            if success:
                console.print(f"[green]✓ Pipeline set to {args.pipeline_type}[/green]")
            else:
                console.print("[red]✗ Failed to set pipeline[/red]")

        elif args.command == "history":
            history = controller.get_history(args.limit)

            table = Table(title="Pipeline Configuration History")
            table.add_column("Type", style="cyan")
            table.add_column("Date/Time", style="yellow")
            table.add_column("By", style="magenta")
            table.add_column("Reason", style="white")
            table.add_column("Active", style="green")

            for record in history:
                table.add_row(
                    record["pipeline_type"],
                    record["created_at"],
                    record.get("created_by", "unknown"),
                    record.get("reason", "-"),
                    "✓" if record["is_active"] else "",
                )

            console.print(table)

        elif args.command == "monitor":
            console.print(
                "[cyan]Monitoring pipeline configuration changes... (Ctrl+C to stop)[/cyan]"
            )
            controller.monitor_changes(args.interval)

        elif args.command == "read-sensor":
            if not args.sensor_db:
                console.print("[red]Error: --sensor-db is required for read-sensor command[/red]")
                return

            records = controller.read_sensor_data(args.sensor_db, args.limit)
            console.print(f"[green]Read {len(records)} sensor records (read-only mode)[/green]")

            for record in records[:5]:  # Show first 5 records
                console.print(record)

    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")
        return 1


if __name__ == "__main__":
    exit(main() or 0)
