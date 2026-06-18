import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from src.main import load_tickers

@patch('src.main.download_file_from_gcs')
@patch('src.main.pd.read_csv')
def test_load_tickers_gcs_success(mock_read_csv, mock_download):
    mock_download.return_value = True
    mock_read_csv.return_value = pd.DataFrame([["AAPL"], ["MSFT"]])
    
    tickers = load_tickers("test-bucket")
    assert tickers == ["AAPL", "MSFT"]
    mock_download.assert_called_once_with("test-bucket", "tickers.csv", "tickers.csv")
    mock_read_csv.assert_called_once()

@patch('src.main.download_file_from_gcs')
def test_load_tickers_gcs_failure(mock_download):
    mock_download.return_value = False
    
    tickers = load_tickers("test-bucket")
    # Should use fallback list
    assert tickers == ["AAPL", "MSFT", "GOOGL"]

