import os
import time
import logging
import pandas as pd
from google.cloud import storage
from database import get_stale_tickers, delete_ticker, upsert_prices, vacuum_db
from checker import check_stale_ticker, get_market_cap_usd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_NAME = "prices.db"
TICKERS_CSV = "tickers.csv"
DEAD_TICKERS_CSV = "dead_tickers.csv"

def download_file_from_gcs(bucket_name: str, source_blob_name: str, destination_file_name: str) -> bool:
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    if blob.exists():
        blob.download_to_filename(destination_file_name)
        logger.info(f"Downloaded {source_blob_name}.")
        return True
    return False

def upload_file_to_gcs(bucket_name: str, source_file_name: str, destination_blob_name: str):
    if not os.path.exists(source_file_name):
        return
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    logger.info(f"Uploaded {source_file_name}.")

def load_active_tickers() -> list[str]:
    """Reads active tickers from TICKERS_CSV safely."""
    active_tickers = []
    try:
        if os.path.exists(TICKERS_CSV):
            active_tickers = pd.read_csv(TICKERS_CSV, header=None)[0].tolist()
    except pd.errors.ParserError as e:
        logger.error(f"CSV Parser error reading {TICKERS_CSV}: {e}")
    except OSError as e:
        logger.error(f"OS error reading {TICKERS_CSV}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error reading {TICKERS_CSV}: {e}")
    return active_tickers

def check_and_update_stale_tickers(stale_tickers: list[str], active_tickers: list[str]) -> list[dict]:
    """Inspects stale tickers, removes dead ones, and upserts data for alive ones."""
    dead_tickers = []
    for ticker in stale_tickers:
        try:
            market_cap = get_market_cap_usd(ticker)
        except Exception as e:
            logger.warning(f"Error fetching market cap for {ticker}: {e}")
            market_cap = 0.0

        is_alive, df = check_stale_ticker(ticker)
        
        if (not is_alive) or (market_cap < 2e9):
            reason = "yfinance no data" if not is_alive else f"market cap {market_cap/1e9:.1f}B"
            logger.info(f"Removing ticker: {ticker} ({reason})")
            if ticker in active_tickers:
                active_tickers.remove(ticker)
            dead_tickers.append({"ticker": ticker, "reason": reason})
            delete_ticker(DB_NAME, ticker)
        else:
            logger.info(f"Ticker {ticker} is alive, upserting missing data.")
            upsert_prices(DB_NAME, df)
    return dead_tickers

def save_dead_tickers(dead_tickers: list[dict]):
    """Saves new dead tickers to DEAD_TICKERS_CSV, preserving existing ones."""
    if not dead_tickers:
        return
    dead_df = pd.DataFrame(dead_tickers)
    try:
        if os.path.exists(DEAD_TICKERS_CSV):
            existing_dead_df = pd.read_csv(DEAD_TICKERS_CSV)
            dead_df = pd.concat([existing_dead_df, dead_df], ignore_index=True)
        dead_df.to_csv(DEAD_TICKERS_CSV, index=False)
    except Exception as e:
        logger.error(f"Error updating dead tickers list: {e}")

def main():
    start_time = time.time()
    logger.info("Starting Ticker Checker Job")
    
    bucket_name = os.environ.get("GCS_BUCKET_NAME")
    if not bucket_name:
        logger.error("GCS_BUCKET_NAME not set.")
        return

    # Download required files
    download_file_from_gcs(bucket_name, DB_NAME, DB_NAME)
    download_file_from_gcs(bucket_name, TICKERS_CSV, TICKERS_CSV)
    download_file_from_gcs(bucket_name, DEAD_TICKERS_CSV, DEAD_TICKERS_CSV)
    
    stale_tickers = get_stale_tickers(DB_NAME)
    logger.info(f"Found {len(stale_tickers)} stale tickers.")
    
    active_tickers = load_active_tickers()
    dead_tickers = check_and_update_stale_tickers(stale_tickers, active_tickers)
            
    # Save active tickers
    if active_tickers:
        pd.Series(active_tickers).to_csv(TICKERS_CSV, index=False, header=False)
        
    save_dead_tickers(dead_tickers)
        
    logger.info("Vacuuming database...")
    vacuum_db(DB_NAME)
    
    logger.info("Uploading updated files back to GCS...")
    upload_file_to_gcs(bucket_name, DB_NAME, DB_NAME)
    upload_file_to_gcs(bucket_name, TICKERS_CSV, TICKERS_CSV)
    upload_file_to_gcs(bucket_name, DEAD_TICKERS_CSV, DEAD_TICKERS_CSV)
    
    end_time = time.time()
    logger.info(f"Job completed. Removed {len(dead_tickers)} dead tickers. Time taken: {end_time - start_time:.2f} s.")

if __name__ == "__main__":
    main()
