import sqlite3
import pandas as pd
from typing import List

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

def get_latest_sync_dates(db_path: str) -> dict[str, str]:
    """Returns a dictionary mapping ticker to its latest sync date."""
    conn = sqlite3.connect(db_path)
    try:
        # Check if table exists first
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prices'")
        if not cursor.fetchone():
            return {}
        
        df = pd.read_sql_query('SELECT ticker, MAX(date) AS last_sync FROM prices GROUP BY ticker', conn)
        return dict(zip(df['ticker'], df['last_sync']))
    finally:
        conn.close()

def upsert_prices(db_path: str, df: pd.DataFrame):
    """Robust upsert into the SQLite prices table."""
    if df.empty:
        return
        
    conn = sqlite3.connect(db_path)
    try:
        # Using sqlite's native INSERT OR REPLACE syntax
        # The dataframe should have columns: ticker, date, adj_close
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
    # VACUUM cannot be executed inside a transaction, so we set isolation_level to None
    conn.isolation_level = None
    conn.execute('VACUUM')
    conn.close()
