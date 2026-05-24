from click.testing import CliRunner
import click
import pytest

@click.group()
def cli():
    pass

@cli.command()
@click.option("--name", default="World")
def hello(name: str):
    click.echo(f"Hello, {name}!")

@cli.command()
@click.argument("filename", type=click.Path())
def write_file(filename: str):
    with open(filename, "w") as f:
        f.write("test data")

def test_hello_command():
    """Basic Click command testing with CliRunner."""
    runner = CliRunner()
    result = runner.invoke(cli, ["hello", "--name", "Alice"])
    assert result.exit_code == 0
    assert "Hello, Alice!" in result.output

def test_file_io_isolated():
    """Testing file I/O in an isolated filesystem."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["write-file", "test.txt"])
        assert result.exit_code == 0
        with open("test.txt") as f:
            assert f.read() == "test data"

def test_stdin_input():
    """Testing commands that require stdin prompts."""
    @click.command()
    def prompt():
        name = click.prompt("Name")
        click.echo(f"Hi {name}")

    runner = CliRunner()
    result = runner.invoke(prompt, input="Bob\n")
    assert "Hi Bob" in result.output
