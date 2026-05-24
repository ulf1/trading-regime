import typer
from typing import Optional

app = typer.Typer(help="Modern CLI application using Typer")

@app.command()
def create(
    name: str, 
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
) -> None:
    """Create a new item with the specified NAME."""
    if verbose:
        typer.echo(f"Creating {name} in verbose mode")
    else:
        typer.echo(f"Creating {name}")

@app.command()
def delete(
    item_id: int = typer.Argument(..., help="The unique ID of the item to delete")
) -> None:
    """Delete an item by its ID."""
    typer.echo(f"Deleting item {item_id}")

@app.command()
def list_items() -> None:
    """List all available items."""
    typer.echo("Fetching list of items...")

if __name__ == '__main__':
    app()
