import os
import time
import logging
import pandas as pd
from google.cloud import storage
from database import init_db, get_ticker_count, upsert_prices, vacuum_db
from download import download_missing_data

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_NAME = "prices.db"
TICKERS_CSV = "tickers.csv"

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

def load_tickers(bucket_name: str) -> list[str]:
    """Downloads and reads tickers from GCS TICKERS_CSV, handling exceptions."""
    tickers = []
    if download_file_from_gcs(bucket_name, TICKERS_CSV, TICKERS_CSV):
        try:
            tickers = pd.read_csv(TICKERS_CSV, header=None)[0].tolist()
        except pd.errors.ParserError as e:
            logger.error(f"CSV Parser error reading {TICKERS_CSV}: {e}")
        except OSError as e:
            logger.error(f"OS error reading {TICKERS_CSV}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error reading {TICKERS_CSV}: {e}")
            
    if not tickers:
        logger.info("Using fallback list for testing.")
        tickers = ["AAPL", "MSFT"]
    return tickers

def backfill_tickers(tickers: list[str]) -> int:
    """Checks each ticker's count and downloads missing historical data if < 2000."""
    upserted_count = 0
    for ticker in tickers:
        count = get_ticker_count(DB_NAME, ticker)
        if count < 2000:
            logger.info(f"Ticker {ticker} has {count} points (<2000). Downloading missing data.")
            df = download_missing_data(ticker)
            if not df.empty:
                upsert_prices(DB_NAME, df)
                upserted_count += 1
        else:
            logger.info(f"Ticker {ticker} has {count} points. Skipping.")
    return upserted_count

def main():
    start_time = time.time()
    logger.info("Starting Initial Downloader Job")
    
    bucket_name = os.environ.get("GCS_BUCKET_NAME")
    if not bucket_name:
        logger.error("GCS_BUCKET_NAME not set.")
        return

    download_file_from_gcs(bucket_name, DB_NAME, DB_NAME)
    
    init_db(DB_NAME)
    
    tickers = load_tickers(bucket_name)
    logger.info(f"Checking {len(tickers)} tickers.")
    
    upserted_count = backfill_tickers(tickers)
            
    logger.info("Vacuuming database...")
    vacuum_db(DB_NAME)
    
    logger.info("Uploading database back to GCS...")
    upload_file_to_gcs(bucket_name, DB_NAME, DB_NAME)
    
    end_time = time.time()
    logger.info(f"Job completed. Backfilled {upserted_count} tickers. Time taken: {end_time - start_time:.2f} s.")

if __name__ == "__main__":
    main()
