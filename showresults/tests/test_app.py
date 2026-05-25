import pytest
from unittest.mock import patch
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@patch("app.download_forecasts_db")
@patch("app.get_latest_forecasts")
def test_dashboard_route(mock_get_latest, mock_download, client):
    # Setup mocks
    mock_download.return_value = True
    mock_get_latest.return_value = [
        {
            "ticker": "AAPL",
            "current_date": "2026-05-25",
            "nll": 9.8000,
            "mu_0": 0.2,
            "mu_1": 0.0,
            "mu_2": -0.3,
            "proba_0": 85.0,
            "proba_1": 10.0,
            "proba_2": 5.0,
            "proba_spread": 80.0,
            "expected_return": 0.2,
            "last_price_date": "2026-05-25",
            "last_price_value": 152.5
        },
        {
            "ticker": "MSFT",
            "current_date": "2026-05-25",
            "nll": 22.4000,
            "mu_0": 0.5,
            "mu_1": 0.1,
            "mu_2": -0.1,
            "proba_0": 70.0,
            "proba_1": 20.0,
            "proba_2": 10.0,
            "proba_spread": 60.0,
            "expected_return": 0.4,
            "last_price_date": "2026-05-25",
            "last_price_value": 305.0
        }
    ]

    response = client.get("/")
    assert response.status_code == 200
    
    html = response.data.decode("utf-8")
    assert "Trading Regime Forecasts" in html
    assert "AAPL" in html
    assert "MSFT" in html
    assert "+80.0%" in html
    assert "+0.2%" in html
    assert "+0.4%" in html
    assert "2026-05-25" in html
    assert "Total Tickers" in html
    
    # Check that download_forecasts_db was called once
    mock_download.assert_called_once()
    mock_get_latest.assert_called_once()
