import os
import sqlite3
import logging
from datetime import datetime, timezone
from google.cloud import storage

logger = logging.getLogger(__name__)

DB_NAME = "forecasts.db"
LOCAL_DB_PATH = f"/tmp/{DB_NAME}"
CACHE_THRESHOLD_SECONDS = 3600  # 1 hour caching

def download_forecasts_db() -> bool:
    """
    Downloads forecasts.db from Google Cloud Storage to local /tmp cache
    if the local file is missing, empty, or older than CACHE_THRESHOLD_SECONDS.
    """
    bucket_name = os.environ.get("GCS_BUCKET_NAME")
    if not bucket_name:
        logger.warning("GCS_BUCKET_NAME environment variable not set. Skipping GCS download.")
        return False

    # Check cache freshness
    if os.path.exists(LOCAL_DB_PATH) and os.path.getsize(LOCAL_DB_PATH) > 0:
        file_age = time_since_modification(LOCAL_DB_PATH)
        if file_age < CACHE_THRESHOLD_SECONDS:
            logger.info("Using cached forecasts.db (cache is fresh).")
            return True

    logger.info(f"Local forecasts.db cache is stale or missing. Downloading from bucket: {bucket_name}")
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(DB_NAME)
        if blob.exists():
            # Ensure target directory exists
            os.makedirs(os.path.dirname(LOCAL_DB_PATH), exist_ok=True)
            blob.download_to_filename(LOCAL_DB_PATH)
            logger.info("Successfully refreshed local forecasts.db cache.")
            return True
        else:
            logger.error(f"{DB_NAME} blob not found in bucket {bucket_name}.")
            return False
    except Exception as e:
        logger.error(f"Error downloading {DB_NAME} from GCS: {e}", exc_info=True)
        return False

def time_since_modification(filepath: str) -> float:
    """Returns the age of a file in seconds since last modification."""
    try:
        mtime = os.path.getmtime(filepath)
        return datetime.now().timestamp() - mtime
    except Exception:
        return float('inf')

def get_latest_forecasts(db_path: str = None) -> list[dict]:
    """
    Queries the latest model forecast results for each active ticker.
    Applies column multiplication scaling (* 100) and calculates the spread.
    
    Returns:
        List of formatted dictionaries containing ticker stats.
    """
    if db_path is None:
        # Fallback to current working directory if GCS is not used/fails and local db exists
        db_path = LOCAL_DB_PATH
        if not os.path.exists(db_path):
            if os.path.exists(DB_NAME):
                db_path = DB_NAME
            else:
                logger.warning(f"forecasts.db not found at {LOCAL_DB_PATH} or {DB_NAME}. Returning empty results.")
                return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    WITH RankedResults AS (
        SELECT 
            training_results.current_date,
            ticker,
            nll,
            raw_mu_0, raw_mu_1, raw_mu_2,
            proba_1d_0, proba_1d_1, proba_1d_2,
            last_price_date,
            last_price_value,
            ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY last_price_date DESC) as rn
        FROM training_results
        WHERE nll < -5000.0
    )
    SELECT 
        RankedResults.current_date,
        ticker,
        nll,
        raw_mu_0, raw_mu_1, raw_mu_2,
        proba_1d_0, proba_1d_1, proba_1d_2,
        last_price_date,
        last_price_value
    FROM RankedResults
    WHERE rn = 1;
    """

    results = []
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        import math
        for row in rows:
            # Map raw floats safely
            nll = row["nll"]
            raw_mu_0 = row["raw_mu_0"]
            raw_mu_1 = row["raw_mu_1"]
            raw_mu_2 = row["raw_mu_2"]
            proba_0 = row["proba_1d_0"]
            proba_1 = row["proba_1d_1"]
            proba_2 = row["proba_1d_2"]

            # Mathematical conversions: reconstruct original ordered mu values from raw parameters
            # mu_bear (State 2) = alpha
            # mu_neutral (State 1) = alpha + exp(beta)
            # mu_bull (State 0) = alpha + exp(beta) + exp(gamma)
            mu_2 = raw_mu_0 if raw_mu_0 is not None else None
            mu_1 = raw_mu_0 + math.exp(raw_mu_1) if (raw_mu_0 is not None and raw_mu_1 is not None) else None
            mu_0 = raw_mu_0 + math.exp(raw_mu_1) + math.exp(raw_mu_2) if (raw_mu_0 is not None and raw_mu_1 is not None and raw_mu_2 is not None) else None

            # multiply by 100, format to 1 decimal place
            formatted_mu0 = round(mu_0 * 100.0, 1) if mu_0 is not None else None
            formatted_mu1 = round(mu_1 * 100.0, 1) if mu_1 is not None else None
            formatted_mu2 = round(mu_2 * 100.0, 1) if mu_2 is not None else None

            formatted_proba0 = round(proba_0 * 100.0, 1) if proba_0 is not None else None
            formatted_proba1 = round(proba_1 * 100.0, 1) if proba_1 is not None else None
            formatted_proba2 = round(proba_2 * 100.0, 1) if proba_2 is not None else None

            # computed column: proba0 - proba2
            spread = None
            if proba_0 is not None and proba_2 is not None:
                spread = round((proba_0 - proba_2) * 100.0, 1)
            
            # computed column: expected return
            expected_return = None
            if proba_0 is not None and proba_1 is not None and proba_2 is not None and mu_0 is not None and mu_1 is not None and mu_2 is not None:
                expected_return = round((proba_0 * mu_0 + proba_1 * mu_1 + proba_2 * mu_2) * 100.0, 1)

            results.append({
                "ticker": row["ticker"],
                "current_date": row["current_date"],
                "nll": round(nll, 0) if nll is not None else None,
                "mu_0": formatted_mu0,
                "mu_1": formatted_mu1,
                "mu_2": formatted_mu2,
                "proba_0": formatted_proba0,
                "proba_1": formatted_proba1,
                "proba_2": formatted_proba2,
                "proba_spread": spread,
                "expected_return": expected_return,
                "last_price_date": row["last_price_date"],
                "last_price_value": round(row["last_price_value"], 2) if row["last_price_value"] is not None else None
            })
    except sqlite3.OperationalError as e:
        logger.error(f"SQLite OperationalError in get_latest_forecasts: {e}", exc_info=True)
    finally:
        conn.close()

    return results
