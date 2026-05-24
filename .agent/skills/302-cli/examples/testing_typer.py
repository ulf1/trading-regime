import typer
from typer.testing import CliRunner
import pytest

app = typer.Typer()

@app.command()
def create_user(username: str, age: int = typer.Option(20)):
    if age < 0:
        typer.echo("Age cannot be negative", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"User {username} created with age {age}")

runner = CliRunner()

def test_create_user_success():
    """Test happy path for Typer command."""
    result = runner.invoke(app, ["create-user", "alice", "--age", "25"])
    assert result.exit_code == 0
    assert "User alice created with age 25" in result.output

@pytest.mark.parametrize("args, expected_exit, expected_msg", [
    (["create-user", "bob", "--age", "-5"], 1, "Age cannot be negative"),
    (["create-user", "bob", "--age", "invalid"], 2, "Invalid value"), # Typer/Click type validation
])
def test_create_user_failures(args, expected_exit, expected_msg):
    """Test validation and error paths using parametrization."""
    result = runner.invoke(app, args)
    assert result.exit_code == expected_exit
    assert expected_msg in result.output or expected_msg in result.stderr
