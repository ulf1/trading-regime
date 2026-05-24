import sqlite3
import pandas as pd
from src.database import init_db, insert_initial_data

def test_insert_initial_data(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(str(db_path))
    
    data = pd.DataFrame([
        {'ticker': 'T1', 'date': '2023-01-01', 'adj_close': 100.0},
        {'ticker': 'T2', 'date': '2023-01-01', 'adj_close': 200.0}
    ])
    insert_initial_data(str(db_path), data)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM prices")
    count = cursor.fetchone()[0]
    assert count == 2
    conn.close()
