import sqlite3
import pandas as pd

def get_stale_tickers(db_path: str) -> list[str]:
    """Returns tickers whose max date is older than 3 weeks."""
    conn = sqlite3.connect(db_path)
    try:
        # Check if table exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prices'")
        if not cursor.fetchone():
            return []
            
        df = pd.read_sql_query('''
            SELECT ticker 
            FROM prices 
            GROUP BY ticker 
            HAVING MAX(date) < date('now', '-21 days')
        ''', conn)
        return df['ticker'].tolist()
    finally:
        conn.close()

def delete_ticker(db_path: str, ticker: str):
    """Deletes all records for a specific ticker."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM prices WHERE ticker = ?", (ticker,))
        conn.commit()
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
