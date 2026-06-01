import os
import time
import logging
import pandas as pd
from google.cloud import storage
from database import init_db, upsert_prices, vacuum_db
from sync import split_into_batches, fetch_batch_data

# Configure standard logging for Cloud Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_NAME = "prices.db"
CSV_NAME = "tickers.csv"

def download_file_from_gcs(bucket_name: str, source_blob_name: str, destination_file_name: str) -> bool:
    """Downloads a blob from the bucket. Returns True if successful."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    if blob.exists():
        blob.download_to_filename(destination_file_name)
        logger.info(f"Downloaded {source_blob_name} to {destination_file_name}.")
        return True
    else:
        logger.warning(f"Blob {source_blob_name} does not exist in GCS.")
        return False

def upload_file_to_gcs(bucket_name: str, source_file_name: str, destination_blob_name: str):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    logger.info(f"Uploaded {source_file_name} to {destination_blob_name}.")

def load_tickers(bucket_name: str) -> list[str]:
    """Downloads and reads the tickers CSV from GCS, with a local fallback."""
    tickers = []
    if download_file_from_gcs(bucket_name, CSV_NAME, CSV_NAME):
        try:
            tickers_df = pd.read_csv(CSV_NAME, header=None)
            tickers = tickers_df[0].tolist()
        except pd.errors.ParserError as e:
            logger.error(f"CSV Parser error reading {CSV_NAME}: {e}")
        except OSError as e:
            logger.error(f"OS error reading {CSV_NAME}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error reading {CSV_NAME}: {e}")
    
    if not tickers:
        logger.info("Using fallback hardcoded ticker list for testing.")
        tickers = ["AAPL", "MSFT", "GOOGL"]
    return tickers

def process_tickers(tickers: list[str]) -> int:
    """Processes tickers in batches, fetching and upserting data."""
    batches = split_into_batches(tickers, batch_size=200)
    total_upserted = 0
    
    for i, batch in enumerate(batches):
        logger.info(f"Processing batch {i+1}/{len(batches)}...")
        df = fetch_batch_data(batch, period="10d", interval="1d")
        
        if not df.empty:
            upsert_prices(DB_NAME, df)
            total_upserted += len(df)
            logger.info(f"Upserted {len(df)} rows.")
        else:
            logger.info("No data fetched for this batch.")
    return total_upserted

def main():
    start_time = time.time()
    logger.info("Starting Data Sync Job")
    
    bucket_name = os.environ.get("GCS_BUCKET_NAME")
    if not bucket_name:
        logger.error("GCS_BUCKET_NAME environment variable not set. Exiting.")
        return

    # Attempt to download existing DB
    download_file_from_gcs(bucket_name, DB_NAME, DB_NAME)
    
    # Initialize local SQLite DB schema
    init_db(DB_NAME)
    
    # Read tickers list
    tickers = load_tickers(bucket_name)
    logger.info(f"Loaded {len(tickers)} tickers to process.")
    
    # Process batches
    total_upserted = process_tickers(tickers)
            
    # Cleanup and optimize DB
    logger.info("Vacuuming database...")
    vacuum_db(DB_NAME)
    
    # Upload DB back to GCS
    logger.info("Uploading database back to GCS...")
    upload_file_to_gcs(bucket_name, DB_NAME, DB_NAME)
    
    end_time = time.time()
    logger.info(f"Job completed successfully. Total rows upserted: {total_upserted}. Time taken: {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()
