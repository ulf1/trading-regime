import os
import sqlite3
import pytest
from database import (
    init_forecasts_db,
    get_latest_prices_date,
    get_latest_training_date,
    fetch_active_tickers_data,
    insert_training_run,
    complete_training_run,
    upsert_training_results,
    fetch_last_training_results
)


@pytest.fixture
def temp_prices_db(tmp_path):
    db_file = tmp_path / "prices.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE prices (
            ticker TEXT,
            date DATE,
            adj_close REAL,
            PRIMARY KEY(ticker, date)
        );
    """)
    # Add dummy prices
    data = [
        ("AAPL", "2026-05-01", 150.0),
        ("AAPL", "2026-05-02", 152.0),
        ("AAPL", "2026-05-03", 151.0),
        ("MSFT", "2026-05-01", 300.0),
        ("MSFT", "2026-05-02", 305.0),
        ("MSFT", "2026-05-03", 304.0),
        ("TSLA", "2026-05-01", 180.0), # No price on 2026-05-03 to test active selection
    ]
    cursor.executemany("INSERT INTO prices VALUES (?, ?, ?);", data)
    conn.commit()
    conn.close()
    return str(db_file)

@pytest.fixture
def temp_forecasts_db(tmp_path):
    db_file = tmp_path / "forecasts.db"
    init_forecasts_db(str(db_file))
    return str(db_file)

def test_trigger_queries(temp_prices_db, temp_forecasts_db):
    # Test prices latest date
    latest_price_dt = get_latest_prices_date(temp_prices_db)
    assert latest_price_dt == "2026-05-03"
    
    # Test forecasts latest completed run date (should be None initially)
    latest_run_dt = get_latest_training_date(temp_forecasts_db)
    assert latest_run_dt is None

def test_training_runs_flow(temp_forecasts_db):
    source_timestamp = "2026-05-03"
    
    # Insert run
    insert_training_run(temp_forecasts_db, source_timestamp)
    latest_run_dt = get_latest_training_date(temp_forecasts_db)
    # Status is running, so latest completed should still be None
    assert latest_run_dt is None
    
    # Complete run
    complete_training_run(temp_forecasts_db, source_timestamp)
    latest_run_dt = get_latest_training_date(temp_forecasts_db)
    assert latest_run_dt == "2026-05-03"

def test_fetch_active_tickers_data(temp_prices_db):
    # Fetch active tickers on 2026-05-03
    # AAPL and MSFT should be found, but TSLA should be excluded (it has no price on 2026-05-03)
    # The prices history should include up to 2 entries per ticker (window size = 2)
    records = fetch_active_tickers_data(temp_prices_db, "2026-05-03", window_size=2)
    
    # Check that TSLA is completely excluded
    tickers = {r[0] for r in records}
    assert "AAPL" in tickers
    assert "MSFT" in tickers
    assert "TSLA" not in tickers
    
    # Check window size constraint (2 items per ticker max)
    aapl_records = [r for r in records if r[0] == "AAPL"]
    msft_records = [r for r in records if r[0] == "MSFT"]
    assert len(aapl_records) == 2
    assert len(msft_records) == 2
    
    # Check dates (should be latest dates since we ordered DESC)
    aapl_dates = {r[1] for r in aapl_records}
    assert aapl_dates == {"2026-05-03", "2026-05-02"}

def test_results_storage_and_warm_start(temp_forecasts_db):
    results = [
        (
            "2026-05-03", "AAPL", 120.5, 0.001, -3.5,
            0.9, 0.05, 0.05,
            0.05, 0.9, 0.05,
            0.05, 0.05, 0.9,
            2000, "2026-05-03", 151.0,
            0.8, 0.1, 0.1
        )
    ]

    
    upsert_training_results(temp_forecasts_db, results)
    
    # Fetch warm start parameters
    params = fetch_last_training_results(temp_forecasts_db, "2026-05-03")
    
    assert "AAPL" in params
    assert params["AAPL"]["mu"] == 0.001
    assert params["AAPL"]["raw_sigma"] == -3.5
    assert params["AAPL"]["transition_matrix"][0] == [0.9, 0.05, 0.05]
