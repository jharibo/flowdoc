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
    type=click.Choice(["mermaid", "dot", "png", "svg", "pdf", "html"]),
    default="mermaid",
    help="Output format (default: mermaid)",
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
@click.option(
    "--src-root",
    type=click.Path(exists=True),
    default=None,
    help="Source root for import resolution (defaults to input directory)",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Additional directory names to exclude (can be repeated)",
)
@click.option(
    "--docstrings",
    is_flag=True,
    default=False,
    help="Include docstrings as tooltips (not supported for PNG/PDF)",
)
def generate(
    source: str,
    output_format: str,
    output: str | None,
    direction: str,
    src_root: str | None,
    exclude: tuple[str, ...],
    docstrings: bool,
) -> None:
    """Generate flow diagrams from Python source files."""
    if docstrings and output_format in ("png", "pdf"):
        raise click.ClickException(
            f"--docstrings is not supported with {output_format.upper()} output "
            "(no tooltip support). "
            "Use --format svg, --format html, or --format dot instead."
        )

    source_path = Path(source)
    exclude_set = set(exclude) if exclude else None

    parser = FlowParser()
    try:
        generator = create_generator(
            output_format, direction=direction, include_docstrings=docstrings
        )
    except ImportError as e:
        raise click.ClickException(str(e)) from None
    generated_count = 0

    # Use parse_directory for directory input (cross-module support)
    if source_path.is_dir():
        flows = parser.parse_directory(source_path, src_root=src_root, exclude=exclude_set)
    else:
        # Single file: still use discovery for consistency, then parse_directory
        flows = parser.parse_directory(source_path, src_root=src_root, exclude=exclude_set)

    if not flows:
        click.echo("No flows found in the specified source.", err=True)
        raise SystemExit(1)

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
@click.option(
    "--src-root",
    type=click.Path(exists=True),
    default=None,
    help="Source root for import resolution (defaults to input directory)",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Additional directory names to exclude (can be repeated)",
)
def validate(
    source: str,
    strict: bool,
    src_root: str | None,
    exclude: tuple[str, ...],
) -> None:
    """Validate flow consistency in Python source files."""
    source_path = Path(source)
    exclude_set = set(exclude) if exclude else None

    parser = FlowParser()
    validator = FlowValidator()
    has_errors = False
    has_warnings = False

    flows = parser.parse_directory(source_path, src_root=src_root, exclude=exclude_set)

    if not flows:
        click.echo("No flows found in the specified source.", err=True)
        raise SystemExit(1)

    for flow_data in flows:
        messages = validator.validate(flow_data)

        if messages:
            click.echo(f"\n{flow_data.name}:")
            for msg in messages:
                prefix = msg.severity.upper()
                click.echo(f"  [{prefix}] {msg.message}")
                if msg.severity == "error":
                    has_errors = True
                elif msg.severity == "warning":
                    has_warnings = True

    if not has_errors and not has_warnings:
        click.echo(f"Validated {len(flows)} flow(s) successfully.")

    if has_errors or (strict and has_warnings):
        raise SystemExit(1)
