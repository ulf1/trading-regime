import click

@click.group()
@click.version_option()
@click.pass_context
def cli(ctx) -> None:
    """Main CLI group. Use this for multi-command CLI applications."""
    pass

@cli.command()
@click.option('--name', '-n', required=True, help='User name')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.argument('filename', type=click.Path(exists=True))
def process(name: str, verbose: bool, filename: str) -> None:
    """
    Process FILENAME for the specified user.
    """
    if verbose:
        click.echo(f"Processing {filename} for {name}")
    # Implementation here
    click.echo(f"Successfully processed {filename}")

@cli.command()
@click.option('--name', required=True)
def create(name: str) -> None:
    """Create a new item."""
    click.echo(f"Creating {name}")

@cli.command()
def list_items() -> None:
    """List all items."""
    click.echo("Items: item1, item2, item3")

if __name__ == '__main__':
    cli()
