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

def insert_initial_data(db_path: str, df: pd.DataFrame):
    """Robust batch insert/upsert for massive initial historical datasets."""
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
