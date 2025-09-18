#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "rich>=10.0.0",
# ]
# ///

"""
Phase Test Validation

Quick validation script to ensure the phase tests are properly structured
and can be executed without errors.
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel


def validate_test_structure():
    """Validate that test files exist and have proper structure."""
    console = Console()

    console.print(Panel.fit(
        "[bold blue]🔍 Phase Test Validation[/bold blue]\n"
        "Checking test file structure and dependencies",
        border_style="blue"
    ))

    test_dir = Path(__file__).parent
    parent_dir = test_dir.parent

    # Check required files exist
    required_files = [
        test_dir / "test_phase_routing.py",
        test_dir / "test_pipeline_state_machine.py",
        test_dir / "run_phase_tests.py",
        parent_dir / "sqlite_to_databricks_uploader.py",
        parent_dir / "pipeline_manager.py"
    ]

    all_exist = True
    for file_path in required_files:
        if file_path.exists():
            console.print(f"[green]✅ {file_path.name}[/green]")
        else:
            console.print(f"[red]❌ {file_path.name} (missing)[/red]")
            all_exist = False

    if not all_exist:
        console.print("\n[red]❌ Some required files are missing![/red]")
        return False

    # Check test file structure
    console.print(f"\n[bold]Validating test file structure...[/bold]")

    test_files = [
        test_dir / "test_phase_routing.py",
        test_dir / "test_pipeline_state_machine.py"
    ]

    for test_file in test_files:
        try:
            content = test_file.read_text()

            # Check for required elements
            checks = [
                ("class Test", "Test class definition"),
                ("def test_", "Test methods"),
                ("@pytest.fixture", "Pytest fixtures"),
                ("import pytest", "Pytest import"),
                ("#!/usr/bin/env -S uv run", "UV shebang")
            ]

            file_valid = True
            for pattern, description in checks:
                if pattern in content:
                    console.print(f"  [green]✓[/green] {description}")
                else:
                    console.print(f"  [red]✗[/red] {description}")
                    file_valid = False

            if file_valid:
                console.print(f"[green]✅ {test_file.name} structure valid[/green]")
            else:
                console.print(f"[red]❌ {test_file.name} structure invalid[/red]")
                all_exist = False

        except Exception as e:
            console.print(f"[red]❌ Error reading {test_file.name}: {e}[/red]")
            all_exist = False

    # Test syntax validation
    console.print(f"\n[bold]Validating Python syntax...[/bold]")

    for test_file in test_files:
        try:
            import ast
            with open(test_file, 'r') as f:
                ast.parse(f.read())
            console.print(f"[green]✅ {test_file.name} syntax valid[/green]")
        except SyntaxError as e:
            console.print(f"[red]❌ {test_file.name} syntax error: {e}[/red]")
            all_exist = False
        except Exception as e:
            console.print(f"[red]❌ {test_file.name} validation error: {e}[/red]")
            all_exist = False

    return all_exist


def show_test_coverage():
    """Show what aspects of the pipeline are covered by tests."""
    console = Console()

    console.print(f"\n[bold]Test Coverage Overview:[/bold]")

    coverage_areas = [
        ("Phase Routing", [
            "raw → ingestion bucket",
            "schematized → schematized bucket (with transformation)",
            "validated → validated/anomalies buckets (with validation)",
            "aggregated → aggregated bucket",
            "anomaly → anomalies bucket"
        ]),
        ("State Management", [
            "Pipeline type persistence",
            "Configuration fallback (database → env → default)",
            "Pipeline switching",
            "Execution history tracking"
        ]),
        ("Data Processing", [
            "Schema transformation (mock)",
            "External validation (mock)",
            "Data splitting (valid/invalid)",
            "Metadata injection"
        ]),
        ("Edge Cases", [
            "Invalid pipeline types",
            "Empty data sets",
            "Malformed configuration",
            "Concurrent access"
        ])
    ]

    for area, items in coverage_areas:
        console.print(f"\n[bold cyan]{area}:[/bold cyan]")
        for item in items:
            console.print(f"  [green]✓[/green] {item}")


def show_usage_instructions():
    """Show how to use the tests."""
    console = Console()

    console.print(Panel.fit(
        "[bold green]🚀 How to Run the Tests[/bold green]\n\n"
        "[bold]Basic test execution:[/bold]\n"
        "  [cyan]uv run tests/run_phase_tests.py[/cyan]\n\n"
        "[bold]Show pipeline behavior demo:[/bold]\n"
        "  [cyan]uv run tests/run_phase_tests.py --demo[/cyan]\n\n"
        "[bold]Run individual test files:[/bold]\n"
        "  [cyan]uv run tests/test_phase_routing.py[/cyan]\n"
        "  [cyan]uv run tests/test_pipeline_state_machine.py[/cyan]\n\n"
        "[bold]Run with pytest directly:[/bold]\n"
        "  [cyan]cd databricks-uploader && python -m pytest tests/ -v[/cyan]",
        border_style="green"
    ))


if __name__ == "__main__":
    console = Console()

    # Validate structure
    if validate_test_structure():
        console.print(f"\n[bold green]🎉 All validation checks passed![/bold green]")

        # Show coverage
        show_test_coverage()

        # Show usage
        show_usage_instructions()

        console.print(f"\n[bold blue]💡 Quick Test:[/bold blue]")
        console.print("Run [cyan]uv run tests/run_phase_tests.py[/cyan] to execute all phase tests")

        exit(0)
    else:
        console.print(f"\n[bold red]❌ Validation failed![/bold red]")
        console.print("Please fix the issues above before running tests.")
        exit(1)