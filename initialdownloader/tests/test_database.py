import sqlite3
import pandas as pd
from src.database import init_db, get_ticker_count, upsert_prices

def test_get_ticker_count(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(str(db_path))
    
    data = pd.DataFrame([
        {'ticker': 'T1', 'date': '2023-01-01', 'adj_close': 100.0},
        {'ticker': 'T1', 'date': '2023-01-02', 'adj_close': 105.0},
        {'ticker': 'T2', 'date': '2023-01-01', 'adj_close': 200.0}
    ])
    upsert_prices(str(db_path), data)
    
    count_t1 = get_ticker_count(str(db_path), 'T1')
    assert count_t1 == 2
    
    count_t2 = get_ticker_count(str(db_path), 'T2')
    assert count_t2 == 1
    
    count_t3 = get_ticker_count(str(db_path), 'T3')
    assert count_t3 == 0
