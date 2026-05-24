import sqlite3
import pandas as pd

def init_db(db_path: str):
    """Initializes the SQLite schema for the prices table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            ticker TEXT,
            date DATE,
            adj_close REAL,
            PRIMARY KEY (ticker, date)
        )
    ''')
    conn.commit()
    conn.close()

def get_ticker_count(db_path: str, ticker: str) -> int:
    """Returns the number of price points for a specific ticker."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prices'")
        if not cursor.fetchone():
            return 0
            
        cursor.execute("SELECT COUNT(*) FROM prices WHERE ticker = ?", (ticker,))
        return cursor.fetchone()[0]
    finally:
        conn.close()

def upsert_prices(db_path: str, df: pd.DataFrame):
    """Robust upsert into the SQLite prices table."""
    if df.empty:
        return
        
    conn = sqlite3.connect(db_path)
    try:
        data = df[['ticker', 'date', 'adj_close']].values.tolist()
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT OR REPLACE INTO prices (ticker, date, adj_close)
            VALUES (?, ?, ?)
        ''', data)
        conn.commit()
    finally:
        conn.close()

def vacuum_db(db_path: str):
    """Runs VACUUM to optimize the database size."""
    conn = sqlite3.connect(db_path)
    conn.isolation_level = None
    conn.execute('VACUUM')
    conn.close()
