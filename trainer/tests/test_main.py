import os
import sqlite3
import pytest
from unittest.mock import patch, MagicMock
from main import main
from database import init_forecasts_db


@pytest.fixture
def clean_env():
    old_bucket = os.environ.get("GCS_BUCKET_NAME")
    os.environ["GCS_BUCKET_NAME"] = "mock-trading-bucket"
    yield
    if old_bucket is not None:
        os.environ["GCS_BUCKET_NAME"] = old_bucket
    else:
        del os.environ["GCS_BUCKET_NAME"]

def setup_mock_dbs(tmp_path):
    prices_path = tmp_path / "prices.db"
    forecasts_path = tmp_path / "forecasts.db"
    
    # 1. Setup mock prices
    conn = sqlite3.connect(prices_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE prices (
            ticker TEXT,
            date DATE,
            adj_close REAL,
            PRIMARY KEY(ticker, date)
        );
    """)
    # Add dummy prices for 2 tickers covering 5 dates
    data = []
    for ticker in ["AAPL", "MSFT"]:
        for i in range(1, 10):
            data.append((ticker, f"2026-05-0{i}", 100.0 + i))
    cursor.executemany("INSERT INTO prices VALUES (?, ?, ?);", data)
    conn.commit()
    conn.close()
    
    # 2. Setup forecasts
    init_forecasts_db(str(forecasts_path))
    
    return prices_path, forecasts_path

@patch("main.download_file_from_gcs")
@patch("main.upload_file_to_gcs")
def test_main_pipeline_triggered_flow(mock_upload, mock_download, clean_env, tmp_path):
    prices_path, forecasts_path = setup_mock_dbs(tmp_path)
    
    # Force main database constants to point to our test temp paths
    with patch("main.PRICES_DB", str(prices_path)), \
         patch("main.FORECASTS_DB", str(forecasts_path)):
         
        # Run main orchestrator
        main()
        
        # Verify GCS download was attempted for both databases
        assert mock_download.call_count == 2
        
        # Verify GCS upload was attempted for forecasts.db
        mock_upload.assert_any_call("mock-trading-bucket", str(forecasts_path), str(forecasts_path))
        
        # Verify the database has the results and runs recorded
        conn = sqlite3.connect(str(forecasts_path))
        cursor = conn.cursor()
        
        # Should record a completed run for the latest price date 2026-05-09
        cursor.execute("SELECT source_timestamp, status FROM training_runs;")
        runs = cursor.fetchall()
        assert len(runs) == 1
        assert runs[0] == ("2026-05-09", "completed")
        
        # Should record model training outputs for both tickers AAPL and MSFT
        cursor.execute("SELECT ticker, last_price_date, mu_0, mu_1, mu_2, nll FROM training_results;")
        results = cursor.fetchall()
        assert len(results) == 2
        tickers = {r[0] for r in results}
        assert tickers == {"AAPL", "MSFT"}
        
        # NLL should be stored and be a valid float
        for r in results:
            assert isinstance(r[5], float)


            
        conn.close()


@patch("main.download_file_from_gcs")
@patch("main.upload_file_to_gcs")
def test_main_pipeline_no_trigger_flow(mock_upload, mock_download, clean_env, tmp_path):
    prices_path, forecasts_path = setup_mock_dbs(tmp_path)
    
    # Setup previous run as already completed up to the latest date 2026-05-09
    conn = sqlite3.connect(str(forecasts_path))
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO training_runs (source_timestamp, status, started_at, completed_at)
        VALUES ('2026-05-09', 'completed', '2026-05-25', '2026-05-25');
    """)
    conn.commit()
    conn.close()
    
    with patch("main.PRICES_DB", str(prices_path)), \
         patch("main.FORECASTS_DB", str(forecasts_path)):
         
        # Run main orchestrator
        main()
        
        # GCS uploads should not be executed (since training is skipped)
        assert mock_upload.call_count == 0
        
        # Verify no new training results were recorded
        conn = sqlite3.connect(str(forecasts_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM training_results;")
        count = cursor.fetchone()[0]
        assert count == 0
        conn.close()

