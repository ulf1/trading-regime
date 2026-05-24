import os
import sqlite3
import pandas as pd
from src.database import init_db, upsert_prices, get_latest_sync_dates, vacuum_db

def test_init_db(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(str(db_path))
    assert os.path.exists(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prices'")
    assert cursor.fetchone() is not None
    conn.close()

def test_upsert_and_get_latest(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(str(db_path))
    
    data1 = pd.DataFrame([
        {'ticker': 'AAPL', 'date': '2023-01-01', 'adj_close': 100.0},
        {'ticker': 'MSFT', 'date': '2023-01-01', 'adj_close': 200.0}
    ])
    upsert_prices(str(db_path), data1)
    
    dates = get_latest_sync_dates(str(db_path))
    assert dates['AAPL'] == '2023-01-01'
    
    data2 = pd.DataFrame([
        {'ticker': 'AAPL', 'date': '2023-01-02', 'adj_close': 105.0},
    ])
    upsert_prices(str(db_path), data2)
    
    dates = get_latest_sync_dates(str(db_path))
    assert dates['AAPL'] == '2023-01-02'
    
    # Test duplicate key upsert (replace)
    data3 = pd.DataFrame([
        {'ticker': 'AAPL', 'date': '2023-01-02', 'adj_close': 110.0},
    ])
    upsert_prices(str(db_path), data3)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT adj_close FROM prices WHERE ticker='AAPL' AND date='2023-01-02'")
    val = cursor.fetchone()[0]
    assert val == 110.0
    conn.close()
