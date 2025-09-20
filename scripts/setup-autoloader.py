#!/usr/bin/env uv
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "databricks-sql-connector>=3.0.0",
#     "python-dotenv>=1.0.0",
# ]
# ///

"""Setup Auto Loader to ingest S3 data into Databricks tables."""

import os
import sys
from dotenv import load_dotenv
from databricks import sql

# Load environment variables
load_dotenv()

def setup_autoloader():
    """Create Auto Loader jobs to continuously load S3 data."""
    
    # Get Databricks credentials
    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    
    # Extract warehouse ID from HTTP_PATH
    warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID")
    if not warehouse_id:
        http_path = os.getenv("DATABRICKS_HTTP_PATH", "")
        if "/warehouses/" in http_path:
            warehouse_id = http_path.split("/warehouses/")[-1]
    
    catalog = os.getenv("DATABRICKS_DATABASE")
    schema = os.getenv("DATABRICKS_DATABASE")
    
    if not all([host, token, warehouse_id]):
        print("❌ Missing Databricks credentials")
        sys.exit(1)
    
    # Clean up host URL
    host = host.replace("https://", "").replace("http://", "")
    
    print(f"🔄 Setting up Auto Loader for {catalog}.{schema}")
    print(f"📊 Warehouse: {warehouse_id}\n")
    
    # Define Auto Loader configurations for each pipeline
    autoloader_configs = [
        {
            "name": "ingestion",
            "source_bucket": "expanso-databricks-ingestion-us-west-2",
            "target_table": "sensor_readings_ingestion",
            "sql": """
                -- Read JSON files and explode the records array
                INSERT INTO {catalog}.{schema}.sensor_readings_ingestion
                SELECT
                    record.sensor_id,
                    to_timestamp(record.timestamp) as timestamp,
                    CAST(record.temperature AS DOUBLE) as temperature,
                    CAST(record.humidity AS DOUBLE) as humidity,
                    CAST(record.pressure AS DOUBLE) as pressure,
                    CAST(record.voltage AS DOUBLE) as voltage,
                    record.location as location,
                    current_timestamp() as ingested_at
                FROM (
                    SELECT explode(records) as record
                    FROM json.`s3://expanso-databricks-ingestion-us-west-2/ingestion/*/*/*/*/data.json`
                )
                WHERE record.sensor_id IS NOT NULL
            """
        },
        {
            "name": "validated",
            "source_bucket": "expanso-databricks-validated-us-west-2",
            "target_table": "sensor_readings_validated",
            "sql": """
                -- Read JSON files and explode the records array
                INSERT INTO {catalog}.{schema}.sensor_readings_validated
                SELECT
                    record.sensor_id,
                    to_timestamp(record.timestamp) as timestamp,
                    CAST(record.temperature AS DOUBLE) as temperature,
                    CAST(record.humidity AS DOUBLE) as humidity,
                    CAST(record.pressure AS DOUBLE) as pressure,
                    CAST(record.voltage AS DOUBLE) as voltage,
                    record.location as location,
                    current_timestamp() as validated_at
                FROM (
                    SELECT explode(records) as record
                    FROM json.`s3://expanso-databricks-validated-us-west-2/ingestion/*/*/*/*/data.json`
                )
                WHERE record.sensor_id IS NOT NULL
            """
        },
        {
            "name": "enriched",
            "source_bucket": "expanso-databricks-enriched-us-west-2",
            "target_table": "sensor_readings_enriched",
            "sql": """
                -- Read JSON files and explode the records array
                INSERT INTO {catalog}.{schema}.sensor_readings_enriched
                SELECT
                    record.sensor_id,
                    to_timestamp(record.timestamp) as timestamp,
                    CAST(record.temperature AS DOUBLE) as temperature,
                    CAST(record.humidity AS DOUBLE) as humidity,
                    CAST(record.pressure AS DOUBLE) as pressure,
                    CAST(record.voltage AS DOUBLE) as voltage,
                    record.location as location,
                    current_timestamp() as enriched_at
                FROM (
                    SELECT explode(records) as record
                    FROM json.`s3://expanso-databricks-enriched-us-west-2/ingestion/*/*/*/*/data.json`
                )
                WHERE record.sensor_id IS NOT NULL
            """
        },
        {
            "name": "anomalies",
            "source_bucket": "expanso-databricks-anomalies-us-west-2",
            "target_table": "sensor_readings_anomalies",
            "sql": """
                -- Read JSON files and explode the records array
                INSERT INTO {catalog}.{schema}.sensor_readings_anomalies
                SELECT
                    record.sensor_id,
                    to_timestamp(record.timestamp) as timestamp,
                    CAST(record.temperature AS DOUBLE) as temperature,
                    CAST(record.humidity AS DOUBLE) as humidity,
                    CAST(record.pressure AS DOUBLE) as pressure,
                    CAST(record.voltage AS DOUBLE) as voltage,
                    CAST(record.anomaly_flag AS INT) as anomaly_flag,
                    record.anomaly_type,
                    CAST(record.anomaly_score AS DOUBLE) as anomaly_score,
                    record.location as location,
                    current_timestamp() as anomalies_at
                FROM (
                    SELECT explode(records) as record
                    FROM json.`s3://expanso-databricks-anomalies-us-west-2/ingestion/*/*/*/*/data.json`
                )
                WHERE record.sensor_id IS NOT NULL
            """
        },
        {
            "name": "aggregated",
            "source_bucket": "expanso-databricks-aggregated-us-west-2",
            "target_table": "sensor_readings_aggregated",
            "sql": """
                -- Read JSON files and explode the records array
                INSERT INTO {catalog}.{schema}.sensor_readings_aggregated
                SELECT
                    record.sensor_id,
                    to_timestamp(record.window_start) as window_start,
                    to_timestamp(record.window_end) as window_end,
                    CAST(record.avg_temperature AS DOUBLE) as avg_temperature,
                    CAST(record.min_temperature AS DOUBLE) as min_temperature,
                    CAST(record.max_temperature AS DOUBLE) as max_temperature,
                    CAST(record.avg_humidity AS DOUBLE) as avg_humidity,
                    CAST(record.avg_pressure AS DOUBLE) as avg_pressure,
                    CAST(record.avg_vibration AS DOUBLE) as avg_vibration,
                    CAST(record.avg_voltage AS DOUBLE) as avg_voltage,
                    CAST(record.record_count AS INT) as record_count,
                    CAST(record.anomaly_count AS INT) as anomaly_count,
                    current_timestamp() as aggregated_at
                FROM (
                    SELECT explode(records) as record
                    FROM json.`s3://expanso-databricks-aggregated-us-west-2/ingestion/*/*/*/*/data.json`
                )
                WHERE record.sensor_id IS NOT NULL
            """
        }
    ]
    
    try:
        # Connect to Databricks
        with sql.connect(
            server_hostname=host,
            http_path=f"/sql/1.0/warehouses/{warehouse_id}",
            access_token=token
        ) as connection:
            with connection.cursor() as cursor:
                print("🚀 Running COPY INTO commands to load existing data...\n")
                
                for config in autoloader_configs:
                    print(f"📥 Loading {config['name']} pipeline...")
                    print(f"   Source: s3://{config['source_bucket']}/")
                    print(f"   Target: {config['target_table']}")
                    
                    try:
                        # Format the SQL
                        formatted_sql = config['sql'].format(
                            catalog=catalog,
                            schema=schema
                        )
                        
                        # Split and execute statements separately
                        statements = [s.strip() for s in formatted_sql.split(';') if s.strip()]
                        
                        for stmt in statements:
                            if stmt.strip():
                                cursor.execute(stmt)
                        
                        # Check how many records were loaded
                        count_sql = f"SELECT COUNT(*) FROM {catalog}.{schema}.{config['target_table']}"
                        cursor.execute(count_sql)
                        count = cursor.fetchone()[0]
                        
                        print(f"   ✅ Loaded! Table now has {count:,} records\n")
                        
                    except Exception as e:
                        if "No new files" in str(e) or "Path does not exist" in str(e):
                            print(f"   ℹ️  No files found in S3 bucket\n")
                        else:
                            print(f"   ⚠️  Error: {str(e)[:200]}\n")
                
                # Show summary
                print("\n📊 LOADING SUMMARY")
                print("-" * 50)
                
                cursor.execute(f"SHOW TABLES IN {catalog}.{schema}")
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = table[1]
                    if "sensor_data_" in table_name:
                        try:
                            count_sql = f"SELECT COUNT(*) FROM {catalog}.{schema}.{table_name}"
                            cursor.execute(count_sql)
                            count = cursor.fetchone()[0]
                            print(f"{table_name:30} {count:>10,} records")
                        except:
                            print(f"{table_name:30} {'N/A':>10}")
                
                print("\n💡 To set up continuous loading:")
                print("1. Go to Databricks Workflows")
                print("2. Create a new job for each pipeline")
                print("3. Use the COPY INTO commands above")
                print("4. Schedule to run every 5-10 minutes")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_autoloader()
    print("\n✅ Auto Loader setup complete!")