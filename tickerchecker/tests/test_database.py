import sqlite3
import pandas as pd
from src.database import get_stale_tickers, delete_ticker, upsert_prices

def test_get_stale_tickers(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE prices (ticker TEXT, date DATE, adj_close REAL, PRIMARY KEY (ticker, date))''')
    
    # Insert one stale ticker and one fresh ticker
    cursor.execute("INSERT INTO prices VALUES ('STALE', date('now', '-25 days'), 100)")
    cursor.execute("INSERT INTO prices VALUES ('FRESH', date('now', '-5 days'), 100)")
    conn.commit()
    conn.close()
    
    stale = get_stale_tickers(str(db_path))
    assert stale == ['STALE']

def test_delete_ticker(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE prices (ticker TEXT, date DATE, adj_close REAL, PRIMARY KEY (ticker, date))''')
    cursor.execute("INSERT INTO prices VALUES ('T1', '2020-01-01', 100)")
    cursor.execute("INSERT INTO prices VALUES ('T2', '2020-01-01', 100)")
    conn.commit()
    conn.close()
    
    delete_ticker(str(db_path), 'T1')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ticker FROM prices")
    tickers = [row[0] for row in cursor.fetchall()]
    assert 'T1' not in tickers
    assert 'T2' in tickers
    conn.close()
