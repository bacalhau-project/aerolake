FROM python:3.11-slim

# Install system packages for networking and debugging
RUN apt-get update && apt-get install -y \
    curl \
    dnsutils \
    iputils-ping \
    netcat-traditional \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv for Python package management
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy all Python scripts and config files
COPY *.py ./
COPY *.yaml ./

# Install Python dependencies using uv
RUN uv pip install --system \
    databricks-sql-connector>=3.0.0 \
    python-dotenv>=1.0.0 \
    boto3>=1.26.0 \
    pyyaml>=6.0 \
    watchdog>=3.0.0 \
    pydantic>=2.0.0 \
    pandas>=2.0.0 \
    sqlalchemy>=2.0.0 \
    click>=8.0.0 \
    requests>=2.28.0 \
    jsonschema>=4.0.0 \
    python-dateutil>=2.8.0 \
    rich>=13.0.0 \
    python-json-logger>=2.0.0 \
    tenacity>=8.0.0 \
    semantic-version>=2.10.0 \
    tabulate>=0.9.0

# Create directories for runtime
RUN mkdir -p /app/state /bacalhau_data/credentials

# Default entrypoint
ENV PYTHONUNBUFFERED=1

# Default entrypoint
ENTRYPOINT ["python", "-u", "sqlite_to_databricks_uploader.py"]

# Default command (can be overridden)
CMD ["--config", "/app/config.yaml"]