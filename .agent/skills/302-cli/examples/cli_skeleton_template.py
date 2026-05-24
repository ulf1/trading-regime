#!/usr/bin/env python3
"""
My awesome CLI application.

Usage:
    my-cli --help
    my-cli create --name "item name"
    my-cli list --verbose
"""

import sys
import logging
from pathlib import Path

import click
from rich.console import Console

# Setup
console = Console()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """My awesome CLI tool."""
    pass


@cli.command()
@click.option('--name', '-n', required=True, help='Item name')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def create(name: str, verbose: bool) -> None:
    """Create a new item."""
    try:
        if verbose:
            console.print(f"Creating item: {name}", style="bold blue")
        console.print(f"✓ Created '{name}' successfully", style="bold green")
    except (ValueError, RuntimeError) as e:
        console.print(f"✗ Error: {e}", style="bold red")
        sys.exit(1)


@cli.command()
@click.option('--limit', '-l', default=10, type=int, help='Max items to show')
def list_items(limit: int) -> None:
    """List all items."""
    try:
        console.print(f"Showing up to {limit} items", style="blue")
    except (ValueError, IndexError) as e:
        console.print(f"✗ Error: {e}", style="bold red")
        sys.exit(1)


if __name__ == '__main__':
    cli()
