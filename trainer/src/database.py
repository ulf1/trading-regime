import sqlite3
import logging
from datetime import datetime, timezone

from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

def init_forecasts_db(db_path: str) -> None:
    """
    Initializes the schema for forecasts.db if it doesn't already exist.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS training_runs (
        source_timestamp TIMESTAMP PRIMARY KEY,
        status TEXT,
        started_at TIMESTAMP,
        completed_at TIMESTAMP
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS training_results (
        current_date DATE,
        ticker TEXT,
        nll DOUBLE PRECISION,
        mu DOUBLE PRECISION,
        raw_sigma DOUBLE PRECISION,
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
    
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS ix_hist
    ON training_results(
        ticker,
        last_price_date
    );
    """)
    
    conn.commit()
    conn.close()
    logger.info("Initialized forecasts.db schema.")

def get_latest_prices_date(prices_db_path: str) -> Optional[str]:
    """
    Returns the maximum date present in prices.db.
    """
    conn = sqlite3.connect(prices_db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT MAX(date) FROM prices;")
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.OperationalError:
        logger.warning("Prices table does not exist or prices.db is empty.")
        return None
    finally:
        conn.close()

def get_latest_training_date(forecasts_db_path: str) -> Optional[str]:
    """
    Returns the maximum source_timestamp in training_runs for completed runs.
    """
    conn = sqlite3.connect(forecasts_db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT MAX(source_timestamp) FROM training_runs WHERE status = 'completed';")
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.OperationalError:
        return None
    finally:
        conn.close()

def fetch_active_tickers_data(prices_db_path: str, last_data_dt: str, window_size: int = 2000) -> List[Tuple[str, str, float]]:
    """
    Finds all tickers active on the last_data_dt, and fetches up to
    the last `window_size` days of adjusted close price data for each of them.
    
    Returns:
        A list of tuples: (ticker, date, adj_close)
    """
    conn = sqlite3.connect(prices_db_path)
    cursor = conn.cursor()
    
    # 1. Fetch active tickers
    cursor.execute("SELECT DISTINCT ticker FROM prices WHERE date = ?;", (last_data_dt,))
    tickers = [row[0] for row in cursor.fetchall()]
    logger.info(f"Found {len(tickers)} active tickers on {last_data_dt}.")
    
    all_data = []
    # 2. Fetch last N price entries for each active ticker
    for i, ticker in enumerate(tickers):
        cursor.execute("""
            SELECT ticker, date, adj_close 
            FROM prices 
            WHERE ticker = ? 
            ORDER BY date DESC 
            LIMIT ?;
        """, (ticker, window_size))
        all_data.extend(cursor.fetchall())
        
        if (i + 1) % 200 == 0:
            logger.info(f"Loaded price history for {i+1}/{len(tickers)} tickers.")
            
    conn.close()
    return all_data

def insert_training_run(forecasts_db_path: str, source_timestamp: str) -> None:
    """
    Inserts a new record into training_runs with status = 'running'.
    """
    conn = sqlite3.connect(forecasts_db_path)
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
        INSERT OR REPLACE INTO training_runs (source_timestamp, status, started_at, completed_at)
        VALUES (?, 'running', ?, NULL);
    """, (source_timestamp, now_str))
    conn.commit()
    conn.close()

def complete_training_run(forecasts_db_path: str, source_timestamp: str) -> None:
    """
    Updates status of training_run to 'completed' and sets completed_at.
    """
    conn = sqlite3.connect(forecasts_db_path)
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
        UPDATE training_runs 
        SET status = 'completed', completed_at = ?
        WHERE source_timestamp = ?;
    """, (now_str, source_timestamp))
    conn.commit()
    conn.close()


def upsert_training_results(forecasts_db_path: str, results: List[Tuple]) -> None:
    """
    Bulk inserts training results into training_results.
    """
    conn = sqlite3.connect(forecasts_db_path)
    cursor = conn.cursor()
    
    cursor.executemany("""
        INSERT INTO training_results (
            current_date, ticker, nll, mu, raw_sigma,
            p_00, p_01, p_02,
            p_10, p_11, p_12,
            p_20, p_21, p_22,
            t_window, last_price_date, last_price_value,
            proba_1d_0, proba_1d_1, proba_1d_2
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, results)

    
    conn.commit()
    conn.close()
    logger.info(f"Successfully upserted {len(results)} results to training_results.")

def fetch_last_training_results(forecasts_db_path: str, last_run_dt: str) -> dict:
    """
    Loads previous model parameters from training_results for warm-starting.
    """
    conn = sqlite3.connect(forecasts_db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT ticker, mu, raw_sigma,
                   p_00, p_01, p_02,
                   p_10, p_11, p_12,
                   p_20, p_21, p_22
            FROM training_results
            WHERE training_results.current_date = ?;
        """, (last_run_dt,))
        rows = cursor.fetchall()

        
        results = {}
        for r in rows:
            results[r[0]] = {
                'mu': r[1],
                'raw_sigma': r[2],
                'transition_matrix': [
                    [r[3], r[4], r[5]],
                    [r[6], r[7], r[8]],
                    [r[9], r[10], r[11]]
                ]
            }
        return results
    except Exception as e:
        logger.error(f"Error fetching training results: {e}", exc_info=True)
        return {}
    finally:
        conn.close()


