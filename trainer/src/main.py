import os
import time
import logging
from datetime import datetime
import pandas as pd
import numpy as np
import torch
from google.cloud import storage

from database import (
    init_forecasts_db,
    get_latest_prices_date,
    get_latest_training_date,
    fetch_active_tickers_data,
    insert_training_run,
    complete_training_run,
    upsert_training_results,
    fetch_last_training_results
)
from dataset import prepare_training_data
from model import MarkovRegimeSwitching, train_mrs_model

# Force float64 for absolute numerical stability
torch.set_default_dtype(torch.float64)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PRICES_DB = "prices.db"
FORECASTS_DB = "forecasts.db"
WINDOW_SIZE = 2000

def download_file_from_gcs(bucket_name: str, source_blob_name: str, destination_file_name: str) -> bool:
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    if blob.exists():
        blob.download_to_filename(destination_file_name)
        logger.info(f"Downloaded {source_blob_name} from GCS.")
        return True
    return False

def upload_file_to_gcs(bucket_name: str, source_file_name: str, destination_blob_name: str):
    if not os.path.exists(source_file_name):
        logger.warning(f"File {source_file_name} does not exist. Skipping GCS upload.")
        return
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    logger.info(f"Uploaded {source_file_name} to GCS.")

def warm_start_model(model: MarkovRegimeSwitching, tickers: list[str], previous_params: dict):
    """
    Overwrites initial random parameters with the trained parameters of the previous run.
    """
    if not previous_params:
        logger.info("No previous parameters found for warm-starting. Using random initialization.")
        return

    logger.info("Applying warm-start parameters...")
    with torch.no_grad():
        for idx, ticker in enumerate(tickers):
            if ticker in previous_params:
                params = previous_params[ticker]
                # raw_mu: (N, K)
                # raw_sigma: (N, K)
                # raw_trans_mat: (N, K, K)
                # Warm start all 3 states of raw_mu
                model.raw_mu[idx, 0] = params['raw_mu_0']
                model.raw_mu[idx, 1] = params['raw_mu_1']
                model.raw_mu[idx, 2] = params['raw_mu_2']
                
                # Warm start all 3 states of raw_sigma
                model.raw_sigma[idx, 0] = params['raw_sigma_0']
                model.raw_sigma[idx, 1] = params['raw_sigma_1']
                model.raw_sigma[idx, 2] = params['raw_sigma_2']

                
                # If we have previous transition matrix details, fill the logits
                p = params['transition_matrix'] # shape (3, 3)
                model.raw_trans_mat[idx] = torch.log(torch.tensor(p, dtype=torch.float64) + 1e-12)

def main():
    start_time = time.time()
    logger.info("Starting Daily Markov Regime Trainer Job")
    
    bucket_name = os.environ.get("GCS_BUCKET_NAME")
    if not bucket_name:
        logger.error("GCS_BUCKET_NAME environment variable not set. Exiting.")
        return

    # 1. Download database assets from GCS
    download_file_from_gcs(bucket_name, PRICES_DB, PRICES_DB)
    download_file_from_gcs(bucket_name, FORECASTS_DB, FORECASTS_DB)
    
    # Initialize forecasts.db schema if it is a fresh local database
    init_forecasts_db(FORECASTS_DB)
    
    # 2. Query last dates and verify trigger logic
    last_data_dt = get_latest_prices_date(PRICES_DB)
    last_run_dt = get_latest_training_date(FORECASTS_DB) # canbe None on first run
    
    logger.info(f"Latest prices date (last_data_dt): {last_data_dt}")
    logger.info(f"Latest completed training date (last_run_dt): {last_run_dt}")
    
    if not last_data_dt:
        logger.error("No historical data found in prices.db. Exiting.")
        return
    elif not last_run_dt:
        logger.info("No previous training run found. Proceeding with training.")
    else: 
        try:
            # Check trigger: last_data_dt > last_run_dt + 1 day
            dt_data = datetime.strptime(last_data_dt, "%Y-%m-%d")
            dt_run = datetime.strptime(last_run_dt, "%Y-%m-%d")
            delta = dt_data - dt_run
            if delta.days <= 1:
                logger.info("Trigger condition not met (last_data_dt is not > last_run_dt + 1 day). Exiting cleanly.")
                return
        except ValueError as e:
            logger.error(f"Error parsing dates: {e}. Proceeding with training anyway.")


    # 3. Trigger training run
    insert_training_run(FORECASTS_DB, last_data_dt)
    
    # 4. Load raw price records
    logger.info(f"Fetching active tickers and historical data up to {WINDOW_SIZE} days...")
    raw_records = fetch_active_tickers_data(PRICES_DB, last_data_dt, window_size=WINDOW_SIZE)
    if not raw_records:
        logger.error(f"No price records found for active tickers on {last_data_dt}. Exiting.")
        return
        
    df_raw = pd.DataFrame(raw_records, columns=["ticker", "date", "adj_close"])
    df_raw.sort_values(by=["ticker", "date"], ascending=[True, True], inplace=True)  # df_raw is anti-chronological, so reverse it
    
    # Get last price mapping for outputs
    df_last_price = df_raw.groupby("ticker").last().reset_index()
    last_price_map = {row["ticker"]: (row["date"], row["adj_close"]) for _, row in df_last_price.iterrows()}
    
    # 5. Preprocess dataset into log returns
    logger.info("Transforming prices to log returns...")
    try:
        df_returns, df_prices = prepare_training_data(df_raw)
    except Exception as e:
        logger.error(f"Error during preprocessing: {e}. Exiting.")
        return
        
    tickers = df_returns.columns.tolist()
    N = len(tickers)
    T = len(df_returns)
    logger.info(f"Prepared returns matrix of shape ({T}, {N}) for {N} tickers.")
    
    # Convert returns DataFrame to double precision PyTorch Tensor
    y_tensor = torch.tensor(df_returns.values, dtype=torch.float64)
    
    # 6. Instantiate and initialize model
    model = MarkovRegimeSwitching(num_series=N, num_states=3)
    
    # Apply warm-start parameters from last successful run if available
    if last_run_dt:
        prev_params = fetch_last_training_results(FORECASTS_DB, last_run_dt)
        warm_start_model(model, tickers, prev_params)
        
    # 7. Train Markov Regime model
    logger.info("Training 3-state Markov Regime-Switching model via autograd...")
    trained_model, losses = train_mrs_model(model, y_tensor, epochs=150, lr=0.05)
    

    
    # 8. Inference and forecasts
    logger.info("Performing final inference and 1-day ahead forecasting...")
    trained_model.eval()
    with torch.no_grad():
        mu, sigma, trans_mat = trained_model.get_constrained_params()
        _, filtered_probs, individual_nlls = trained_model(y_tensor)

        
        # Latest filtered probabilities: shape (N, 3)
        last_state_prob = filtered_probs[-1]
        
        # Predict t+1 state probabilities: shape (N, 3)
        next_state_prob = torch.bmm(last_state_prob.unsqueeze(1), trans_mat).squeeze(1)
        
    # 9. Format outputs for database persistence
    results_list = []
    for idx, ticker in enumerate(tickers):
        # Retrieve last price info
        last_date, last_val = last_price_map.get(ticker, (last_data_dt, 0.0))
        
        # Extract all 3 states of raw_mu
        raw_mu_0 = trained_model.raw_mu[idx, 0].item()
        raw_mu_1 = trained_model.raw_mu[idx, 1].item()
        raw_mu_2 = trained_model.raw_mu[idx, 2].item()
        
        # Extract all 3 states of raw_sigma
        sig_0 = trained_model.raw_sigma[idx, 0].item()
        sig_1 = trained_model.raw_sigma[idx, 1].item()
        sig_2 = trained_model.raw_sigma[idx, 2].item()
        
        # Transition matrix elements
        p = trans_mat[idx] # (3, 3)
        
        # Predicted probabilities
        p_next_0 = next_state_prob[idx, 0].item()
        p_next_1 = next_state_prob[idx, 1].item()
        p_next_2 = next_state_prob[idx, 2].item()
        
        # Individual negative log-likelihood
        ticker_nll = individual_nlls[idx].item()
        
        results_list.append((
            last_data_dt,
            ticker,
            ticker_nll,
            raw_mu_0,
            raw_mu_1,
            raw_mu_2,
            sig_0,
            sig_1,
            sig_2,
            p[0, 0].item(), p[0, 1].item(), p[0, 2].item(), # State 0 transitions
            p[1, 0].item(), p[1, 1].item(), p[1, 2].item(), # State 1 transitions
            p[2, 0].item(), p[2, 1].item(), p[2, 2].item(), # State 2 transitions
            WINDOW_SIZE,
            last_date,
            last_val,
            p_next_0,
            p_next_1,
            p_next_2
        ))

        
    # Write to local forecasts.db
    logger.info(f"Upserting {len(results_list)} results to local {FORECASTS_DB}...")
    upsert_training_results(FORECASTS_DB, results_list)
    
    # Mark run as completed
    complete_training_run(FORECASTS_DB, last_data_dt)
    
    # 10. Upload updated forecasts.db back to GCS
    logger.info("Uploading updated forecasts.db back to GCS...")
    upload_file_to_gcs(bucket_name, FORECASTS_DB, FORECASTS_DB)
    
    end_time = time.time()
    logger.info(f"Trainer Job completed successfully in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()
