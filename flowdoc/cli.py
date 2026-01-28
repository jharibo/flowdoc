"""Command-line interface for FlowDoc.

Provides ``flowdoc generate`` and ``flowdoc validate`` commands.
"""

from __future__ import annotations

import re
from pathlib import Path

import click

from flowdoc.generator import create_generator
from flowdoc.parser import FlowParser
from flowdoc.validator import FlowValidator


def _slugify(name: str) -> str:
    """Convert a flow name to a filesystem-safe slug.

    Strips non-word characters and replaces whitespace/hyphens with underscores.

    :param name: Flow display name
    :return: Lowercased filesystem-safe slug
    """
    slug = name.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "_", slug)
    return slug.strip("_")


def _collect_python_files(source: Path) -> list[Path]:
    """Collect Python files from a path (file or directory).

    :param source: File or directory path
    :return: List of Python file paths
    """
    if source.is_file():
        return [source]
    if source.is_dir():
        return sorted(source.rglob("*.py"))
    return []


@click.group()
@click.version_option(package_name="flowdoc")
def cli() -> None:
    """FlowDoc - Generate business flow diagrams from Python code."""


@cli.command()
@click.argument("source", type=click.Path(exists=True))
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["png", "svg", "pdf", "dot", "mermaid"]),
    default="png",
    help="Output format (default: png)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output file path",
)
@click.option(
    "--direction",
    "-d",
    type=click.Choice(["TB", "LR"]),
    default="TB",
    help="Layout direction (default: TB)",
)
def generate(source: str, output_format: str, output: str | None, direction: str) -> None:
    """Generate flow diagrams from Python source files."""
    source_path = Path(source)
    files = _collect_python_files(source_path)

    if not files:
        click.echo(f"No Python files found in {source}", err=True)
        raise SystemExit(1)

    parser = FlowParser()
    generator = create_generator(output_format, direction=direction)
    generated_count = 0

    for file_path in files:
        try:
            flows = parser.parse_file(file_path)
        except SyntaxError as e:
            click.echo(f"Error parsing {file_path}: {e}", err=True)
            continue

        if not flows:
            continue

        for flow_data in flows:
            if output:
                output_path = Path(output)
            else:
                slug = _slugify(flow_data.name)
                output_path = Path(slug)

            try:
                result = generator.generate(flow_data, output_path)
                click.echo(f"Generated: {result}")
                generated_count += 1
            except Exception as e:
                click.echo(f"Error generating diagram for '{flow_data.name}': {e}", err=True)

    if generated_count == 0:
        click.echo("No flows found in the specified source.", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("source", type=click.Path(exists=True))
@click.option(
    "--strict",
    is_flag=True,
    help="Exit with error code on warnings",
)
def validate(source: str, strict: bool) -> None:
    """Validate flow consistency in Python source files."""
    source_path = Path(source)
    files = _collect_python_files(source_path)

    if not files:
        click.echo(f"No Python files found in {source}", err=True)
        raise SystemExit(1)

    parser = FlowParser()
    validator = FlowValidator()
    has_errors = False
    has_warnings = False
    flow_count = 0

    for file_path in files:
        try:
            flows = parser.parse_file(file_path)
        except SyntaxError as e:
            click.echo(f"Error parsing {file_path}: {e}", err=True)
            has_errors = True
            continue

        for flow_data in flows:
            flow_count += 1
            messages = validator.validate(flow_data)

            if messages:
                click.echo(f"\n{flow_data.name} ({file_path}):")
                for msg in messages:
                    prefix = msg.severity.upper()
                    click.echo(f"  [{prefix}] {msg.message}")
                    if msg.severity == "error":
                        has_errors = True
                    elif msg.severity == "warning":
                        has_warnings = True

    if flow_count == 0:
        click.echo("No flows found in the specified source.", err=True)
        raise SystemExit(1)

    if not has_errors and not has_warnings:
        click.echo(f"Validated {flow_count} flow(s) successfully.")

    if has_errors or (strict and has_warnings):
        raise SystemExit(1)
