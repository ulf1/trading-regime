import os
import time
import logging
import pandas as pd
from google.cloud import storage
from database import init_db, insert_initial_data
from scraper import scrape_new_tickers, fetch_historical_data

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

def main():
    start_time = time.time()
    logger.info("Starting Find Ticker Job")
    
    bucket_name = os.environ.get("GCS_BUCKET_NAME")
    if not bucket_name:
        logger.error("GCS_BUCKET_NAME not set.")
        return

    download_file_from_gcs(bucket_name, DB_NAME, DB_NAME)
    download_file_from_gcs(bucket_name, TICKERS_CSV, TICKERS_CSV)
    
    init_db(DB_NAME)
    
    existing_tickers = set()
    if os.path.exists(TICKERS_CSV):
        try:
            existing_tickers = set(pd.read_csv(TICKERS_CSV, header=None)[0].tolist())
        except Exception as e:
            logger.error(f"Error reading {TICKERS_CSV}: {e}")
            
    scraped_tickers = scrape_new_tickers(top_n=50) # Increased to 50 for better discovery
    logger.info(f"Scraped {len(scraped_tickers)} most active tickers.")
    
    new_tickers = [t for t in scraped_tickers if t not in existing_tickers]
    
    if not new_tickers:
        logger.info("No new tickers discovered. Exiting cleanly.")
        return
        
    logger.info(f"Discovered {len(new_tickers)} new tickers: {new_tickers}")
    
    for ticker in new_tickers:
        df = fetch_historical_data(ticker)
        if not df.empty:
            insert_initial_data(DB_NAME, df)
            existing_tickers.add(ticker)
            
    # Save updated tickers.csv
    pd.Series(list(existing_tickers)).to_csv(TICKERS_CSV, index=False, header=False)
    
    logger.info("Uploading updated files back to GCS...")
    upload_file_to_gcs(bucket_name, DB_NAME, DB_NAME)
    upload_file_to_gcs(bucket_name, TICKERS_CSV, TICKERS_CSV)
    
    end_time = time.time()
    logger.info(f"Job completed. Discovered and initialized {len(new_tickers)} new tickers. Time taken: {end_time - start_time:.2f} s.")

if __name__ == "__main__":
    main()
