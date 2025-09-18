# Pipeline Phase Testing Suite

This directory contains lightweight unit tests for validating the databricks uploader phase routing logic without requiring actual S3 uploads or external dependencies.

## 📁 Test Files

### Core Test Files
- **`test_phase_logic_simple.py`** - Lightweight tests for pipeline phase logic and bucket routing
- **`test_pipeline_state_machine.py`** - Tests pipeline configuration management
- **`run_phase_tests.py`** - Test runner with reporting capabilities
- **`validate_phase_tests.py`** - Test structure validation
- **`test_phase_routing.py`** - Advanced tests with full uploader mocking (experimental)

## 🎯 What These Tests Validate

### Phase Routing Logic
Each pipeline phase correctly routes data to the appropriate S3 bucket:

| Phase | Processing | Valid → | Invalid → | Split Behavior |
|-------|------------|---------|-----------|----------------|
| `raw` | Pass-through, no validation | ingestion | N/A | No splitting |
| `schematized` | Transform to turbine schema | schematized | N/A | No splitting |
| `validated` | External JSON schema validation | validated | anomalies | **SPLIT** |
| `aggregated` | Basic aggregation | aggregated | N/A | No splitting |
| `anomaly` | Direct anomaly routing | anomalies | N/A | No splitting |

### State Management
- Pipeline type persistence in SQLite database
- Configuration fallback: database → environment → default
- Pipeline switching and execution history
- Concurrent access scenarios

### Data Processing
- Schema transformation (mocked)
- External validation with splitting (mocked)
- Metadata injection
- Error handling for invalid configurations

## 🚀 Running the Tests

### Quick Test Execution
```bash
# Run all phase tests with reporting
uv run tests/run_phase_tests.py

# Show pipeline behavior demo
uv run tests/run_phase_tests.py --demo

# Validate test structure
uv run tests/validate_phase_tests.py
```

### Individual Test Files
```bash
# Test phase routing logic (simplified)
uv run tests/test_phase_logic_simple.py

# Test state machine behavior
uv run tests/test_pipeline_state_machine.py

# Test advanced phase routing (experimental)
uv run tests/test_phase_routing.py
```

### Using pytest directly
```bash
cd databricks-uploader
python -m pytest tests/ -v
```

## 🧪 Test Architecture

### Mocking Strategy
The tests use comprehensive mocking to avoid external dependencies:

- **S3 Operations**: `_upload_to_s3()` method mocked
- **AWS Credentials**: Test credentials provided in config
- **SQLite Database**: Temporary databases created for each test
- **State Directories**: Temporary directories with proper cleanup
- **External Schema**: Mock JSON schema validation
- **Node Identity**: Fixed test node ID

### Test Data
Sample environmental sensor data with known anomalies:
- **Normal record**: temperature=22.5°C, humidity=65%
- **Temperature anomaly**: temperature=-50°C (too cold)
- **Humidity anomaly**: humidity=120% (impossible)

## ✅ Test Coverage

### Phase Logic Tests (`test_phase_logic_simple.py`)
- ✓ Raw phase routing (no processing)
- ✓ Schematized phase routing (transformation only)
- ✓ Validated phase routing (with schema validation splitting)
- ✓ Aggregated phase routing
- ✓ Anomaly phase routing
- ✓ Bucket mapping completeness
- ✓ Pipeline type switching
- ✓ Invalid pipeline type handling
- ✓ Empty data handling
- ✓ All bucket mappings (parametrized test)

### State Machine Tests (`test_pipeline_state_machine.py`)
- ✓ Initial state with defaults
- ✓ Environment variable override
- ✓ Pipeline type persistence
- ✓ Cross-instance persistence
- ✓ Pipeline switching
- ✓ Execution recording and history
- ✓ Database schema creation
- ✓ Configuration source priority
- ✓ Execution history limits
- ✓ Concurrent access safety
- ✓ Malformed data handling

## 🔧 Key Features

### Lightweight Design
- No actual S3 uploads required
- No external service dependencies
- Fast execution (< 1 second total)
- Comprehensive mocking

### Production Alignment
- Tests actual production code paths
- Validates real pipeline configurations
- Matches bucket mapping logic
- Tests state management behavior

### Developer Friendly
- Clear test names and documentation
- Rich reporting with colored output
- Individual test execution
- Validation tools for setup verification

## 🛠️ Implementation Notes

### Pipeline Phase Logic
The tests validate the core `_validate_and_split_data()` method which:
1. Reads current pipeline type from state manager
2. Applies appropriate processing based on phase
3. Returns valid/invalid record splits
4. Routes to correct S3 buckets via bucket mapping

### State Machine Logic
The tests validate the `PipelineManager` class which:
1. Persists pipeline configuration in SQLite
2. Provides configuration fallback hierarchy
3. Records execution history with metadata
4. Supports atomic pipeline type switching

### Bucket Routing
The pipeline uses this bucket mapping strategy:
- **Direct mapping**: `raw` → `ingestion`, `aggregated` → `aggregated`
- **Split mapping**: `validated` → `SPLIT` (validated + anomalies buckets)
- **Transformation mapping**: `schematized` → `schematized`

## 📊 Expected Test Results

When running `uv run tests/run_phase_tests.py`:

```
🧪 Pipeline Phase Testing Suite
Testing pipeline routing logic without S3 uploads

Running test_phase_logic_simple.py...
✅ test_phase_logic_simple.py passed

Running test_pipeline_state_machine.py...
✅ test_pipeline_state_machine.py passed

🎉 All pipeline phase tests passed!
Pipeline routing logic is working correctly.
```

## 🔍 Troubleshooting

### Common Issues
1. **Import errors**: Ensure you're running from the `databricks-uploader` directory
2. **Permission errors**: Tests create temporary files - ensure write permissions
3. **Dependency errors**: Install test dependencies via uv script headers

### Debug Tips
- Run `validate_phase_tests.py` first to check setup
- Use `-v` flag with pytest for verbose output
- Check individual test files for isolated testing
- Review mocking setup if tests fail unexpectedly

## 🎯 Next Steps

These tests provide a foundation for:
1. **Regression testing** - Validate changes don't break routing logic
2. **Development confidence** - Test new pipeline phases
3. **CI/CD integration** - Automated validation in build pipeline
4. **Performance testing** - Baseline for optimization work

The lightweight design ensures these tests can run quickly in any environment without external dependencies.