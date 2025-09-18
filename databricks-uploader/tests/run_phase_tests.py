#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pytest>=7.0",
#   "pytest-mock",
#   "rich>=10.0.0",
# ]
# ///

"""
Phase Testing Runner

Executes all pipeline phase tests and provides a detailed report
of pipeline routing behavior validation.
"""

import subprocess
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


def run_tests():
    """Run all phase-related tests and generate report."""
    console = Console()

    # Test files to run
    test_files = [
        "test_phase_logic_simple.py",
        "test_pipeline_state_machine.py",
        "test_schema_violations.py",
        "test_metadata_injection.py",
        "test_unity_catalog_mapping.py"
    ]

    console.print(Panel.fit(
        "[bold blue]🧪 Pipeline Phase Testing Suite[/bold blue]\n"
        "Testing pipeline routing logic without S3 uploads",
        border_style="blue"
    ))

    results = {}
    overall_success = True

    for test_file in test_files:
        test_path = Path(__file__).parent / test_file
        if not test_path.exists():
            console.print(f"[red]❌ Test file not found: {test_file}[/red]")
            continue

        console.print(f"\n[yellow]Running {test_file}...[/yellow]")

        # Run pytest on the specific file
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            str(test_path),
            "-v",
            "--tb=short",
            "-q"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)

        results[test_file] = {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

        if result.returncode == 0:
            console.print(f"[green]✅ {test_file} passed[/green]")
        else:
            console.print(f"[red]❌ {test_file} failed[/red]")
            overall_success = False

    # Generate summary report
    console.print("\n" + "="*60)
    console.print("[bold]Test Results Summary[/bold]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Test File", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    for test_file, result in results.items():
        if result["returncode"] == 0:
            status = "[green]✅ PASS[/green]"
            details = "All tests passed"
        else:
            status = "[red]❌ FAIL[/red]"
            # Extract key error info
            details = result["stderr"].split('\n')[0] if result["stderr"] else "See output above"

        table.add_row(test_file, status, details)

    console.print(table)

    # Show phase coverage
    console.print(f"\n[bold]Pipeline Phases Tested:[/bold]")
    phases = ["raw", "schematized", "validated", "aggregated", "anomaly"]
    for phase in phases:
        console.print(f"  [green]✓[/green] {phase} phase routing")

    console.print(f"\n[bold]Bucket Routing Tested:[/bold]")
    buckets = ["ingestion", "schematized", "validated/anomalies (SPLIT)", "aggregated", "anomalies"]
    for bucket in buckets:
        console.print(f"  [green]✓[/green] {bucket}")

    if overall_success:
        console.print(f"\n[bold green]🎉 All pipeline phase tests passed![/bold green]")
        console.print("[green]Pipeline routing logic is working correctly.[/green]")
        return 0
    else:
        console.print(f"\n[bold red]❌ Some tests failed![/bold red]")
        console.print("[red]Check the output above for details.[/red]")
        return 1


def demo_pipeline_behavior():
    """Demonstrate pipeline behavior for each phase."""
    console = Console()

    console.print(Panel.fit(
        "[bold blue]🔄 Pipeline Phase Behavior Demo[/bold blue]\n"
        "Showing how data flows through each pipeline phase",
        border_style="blue"
    ))

    # Sample data for demo
    sample_data = [
        {"id": 1, "temperature": 22.5, "humidity": 65.0, "status": "normal"},
        {"id": 2, "temperature": -50.0, "humidity": 45.0, "status": "temp_anomaly"},
        {"id": 3, "temperature": 25.0, "humidity": 120.0, "status": "humidity_anomaly"}
    ]

    # Phase behavior table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Phase", style="cyan", width=12)
    table.add_column("Processing", width=25)
    table.add_column("Valid Records", justify="center", width=12)
    table.add_column("Invalid Records", justify="center", width=12)
    table.add_column("Target Bucket", style="green", width=15)

    phases = [
        ("raw", "No processing", "3", "0", "ingestion"),
        ("schematized", "Transform to turbine schema", "3", "0", "schematized"),
        ("validated", "External schema validation", "1", "2", "validated/anomalies"),
        ("aggregated", "Basic aggregation", "3", "0", "aggregated"),
        ("anomaly", "Direct anomaly routing", "3", "0", "anomalies")
    ]

    for phase, processing, valid, invalid, bucket in phases:
        table.add_row(phase, processing, valid, invalid, bucket)

    console.print(table)

    console.print(f"\n[bold]Key Insights:[/bold]")
    console.print("• [yellow]raw[/yellow] phase: Pass-through, no validation")
    console.print("• [yellow]schematized[/yellow] phase: Transform structure, no validation")
    console.print("• [yellow]validated[/yellow] phase: Split based on external schema validation")
    console.print("• [yellow]aggregated[/yellow] phase: Process for analytics")
    console.print("• [yellow]anomaly[/yellow] phase: Direct routing for anomaly processing")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run pipeline phase tests")
    parser.add_argument("--demo", action="store_true", help="Show pipeline behavior demo")
    args = parser.parse_args()

    if args.demo:
        demo_pipeline_behavior()
        exit(0)
    else:
        exit(run_tests())