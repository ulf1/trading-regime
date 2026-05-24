from unittest.mock import patch, MagicMock
import typer
from typer.testing import CliRunner

app = typer.Typer()

def fetch_data_from_api(url: str):
    # Imagine this uses 'requests' or similar
    import requests
    response = requests.get(url)
    return response.json()

@app.command()
def fetch(url: str):
    data = fetch_data_from_api(url)
    typer.echo(f"Received: {data['status']}")

runner = CliRunner()

def test_fetch_command_mocked():
    """Test a command that depends on an external API by mocking the library."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "success"}

    with patch("requests.get", return_value=mock_response):
        result = runner.invoke(app, ["fetch", "https://api.example.com"])
        assert result.exit_code == 0
        assert "Received: success" in result.output

def test_logic_isolation():
    """
    Demonstrates separating business logic for direct testing.
    Instead of testing via CLI runner, test the core function.
    """
    # core_logic.py
    def calculate_total(price: float, tax: float) -> float:
        return price * (1 + tax)

    # test_core.py (No CliRunner needed)
    assert calculate_total(100.0, 0.1) == 110.0
