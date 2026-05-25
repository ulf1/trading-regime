import os
import sqlite3
import pytest
from database import get_latest_forecasts

@pytest.fixture
def temp_forecasts_db(tmp_path):
    db_file = tmp_path / "forecasts.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Replicate trainer's schema for training_results
    cursor.execute("""
    CREATE TABLE training_results (
        current_date DATE,
        ticker TEXT,
        nll DOUBLE PRECISION,
        mu_0 DOUBLE PRECISION,
        mu_1 DOUBLE PRECISION,
        mu_2 DOUBLE PRECISION,
        raw_sigma_0 DOUBLE PRECISION,
        raw_sigma_1 DOUBLE PRECISION,
        raw_sigma_2 DOUBLE PRECISION,
        p_00 DOUBLE PRECISION,
        p_01 DOUBLE PRECISION,
        p_02 DOUBLE PRECISION,
        p_10 DOUBLE PRECISION,
        p_11 DOUBLE PRECISION,
        p_12 DOUBLE PRECISION,
        p_20 DOUBLE PRECISION,
        p_21 DOUBLE PRECISION,
        p_22 DOUBLE PRECISION,
        t_window INTEGER,
        last_price_date DATE,
        last_price_value DOUBLE PRECISION,
        proba_1d_0 DOUBLE PRECISION,
        proba_1d_1 DOUBLE PRECISION,
        proba_1d_2 DOUBLE PRECISION
    );
    """)
    
    # Insert multiple rows, including duplicate tickers with different dates
    # so we can test that only the LATEST row is fetched.
    data = [
        # Older AAPL run
        ("2026-05-24", "AAPL", 10.5, 0.001, 0.0, -0.002, 0.1, 0.2, 0.3, 0.8, 0.1, 0.1, 0.1, 0.8, 0.1, 0.1, 0.1, 0.8, 2000, "2026-05-24", 150.0, 0.8, 0.1, 0.1),
        # Newer AAPL run (should be fetched)
        ("2026-05-25", "AAPL", 9.8, 0.002, 0.0, -0.003, 0.1, 0.2, 0.3, 0.8, 0.1, 0.1, 0.1, 0.8, 0.1, 0.1, 0.1, 0.8, 2000, "2026-05-25", 152.5, 0.85, 0.1, 0.05),
        
        # MSFT (only one run)
        ("2026-05-25", "MSFT", 22.4, 0.005, 0.001, -0.001, 0.1, 0.2, 0.3, 0.8, 0.1, 0.1, 0.1, 0.8, 0.1, 0.1, 0.1, 0.8, 2000, "2026-05-25", 305.0, 0.7, 0.2, 0.1),
    ]
    
    cursor.executemany("""
        INSERT INTO training_results VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        );
    """, data)
    
    conn.commit()
    conn.close()
    return str(db_file)

def test_get_latest_forecasts(temp_forecasts_db):
    results = get_latest_forecasts(temp_forecasts_db)
    
    # Should get exactly 2 rows (one for AAPL, one for MSFT)
    assert len(results) == 2
    
    # Map results by ticker for easy testing
    res_map = {r["ticker"]: r for r in results}
    assert "AAPL" in res_map
    assert "MSFT" in res_map
    
    # Verify AAPL is the latest row (current_date is 2026-05-25, not 2026-05-24)
    aapl = res_map["AAPL"]
    assert aapl["current_date"] == "2026-05-25"
    assert aapl["nll"] == 9.8
    assert aapl["last_price_value"] == 152.50
    
    # Verify math scaling (* 100) and rounding to 1 decimal place:
    # mu_0 was 0.002 -> 0.002 * 100 = 0.2
    assert aapl["mu_0"] == 0.2
    # mu_2 was -0.003 -> -0.3
    assert aapl["mu_2"] == -0.3
    
    # proba_0 was 0.85 -> 85.0
    assert aapl["proba_0"] == 85.0
    # proba_2 was 0.05 -> 5.0
    assert aapl["proba_2"] == 5.0
    
    # computed column: (proba_0 - proba_2) * 100
    # 0.85 - 0.05 = 0.80 -> 80.0
    assert aapl["proba_spread"] == 80.0

    # Verify MSFT values
    msft = res_map["MSFT"]
    assert msft["current_date"] == "2026-05-25"
    assert msft["nll"] == 22.4
    assert msft["mu_0"] == 0.5
    assert msft["proba_spread"] == 60.0 # (0.7 - 0.1) * 100 = 60.0
