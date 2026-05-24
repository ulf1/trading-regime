import time
import logging
import pandas as pd
import yfinance as yf
from typing import List

logger = logging.getLogger(__name__)

def fetch_batch_data(tickers: List[str], period: str = "10d", interval: str = "1d", max_retries: int = 3) -> pd.DataFrame:
    """
    Fetches data for a batch of tickers using yfinance with retry logic.
    Returns a dataframe formatted for database insertion.
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching data for batch of {len(tickers)} tickers, attempt {attempt + 1}")
            # group_by="ticker" ensures reliable multi-ticker downloads
            data = yf.download(tickers, period=period, interval=interval, group_by="ticker", auto_adjust=False, threads=False, progress=False)
            
            if data.empty:
                logger.warning("No data downloaded for batch.")
                return pd.DataFrame()

            processed_dfs = []
            
            # Handle multi-index columns if multiple tickers, else single ticker format
            if len(tickers) > 1:
                for ticker in tickers:
                    if ticker in data.columns.levels[0]:
                        ticker_df = data[ticker].copy()
                        if 'Adj Close' in ticker_df.columns:
                            ticker_df = ticker_df[['Adj Close']].dropna()
                            ticker_df = ticker_df.reset_index()
                            ticker_df['ticker'] = ticker
                            # Ensure date is string format (YYYY-MM-DD)
                            ticker_df['Date'] = ticker_df['Date'].dt.strftime('%Y-%m-%d')
                            ticker_df = ticker_df.rename(columns={'Date': 'date', 'Adj Close': 'adj_close'})
                            processed_dfs.append(ticker_df)
            else:
                ticker = tickers[0]
                if 'Adj Close' in data.columns:
                    ticker_df = data[['Adj Close']].dropna().copy()
                    ticker_df = ticker_df.reset_index()
                    ticker_df['ticker'] = ticker
                    ticker_df['Date'] = ticker_df['Date'].dt.strftime('%Y-%m-%d')
                    ticker_df = ticker_df.rename(columns={'Date': 'date', 'Adj Close': 'adj_close'})
                    processed_dfs.append(ticker_df)
                    
            if not processed_dfs:
                return pd.DataFrame()
                
            final_df = pd.concat(processed_dfs, ignore_index=True)
            return final_df
            
        except Exception as e:
            logger.error(f"Error fetching batch: {e}")
            if attempt < max_retries - 1:
                backoff_time = 2 ** attempt
                logger.info(f"Retrying in {backoff_time} seconds...")
                time.sleep(backoff_time)
            else:
                logger.error("Max retries exceeded.")
                
    return pd.DataFrame()

def split_into_batches(tickers: List[str], batch_size: int = 200) -> List[List[str]]:
    """Splits a list of tickers into smaller batches."""
    return [tickers[i:i + batch_size] for i in range(0, len(tickers), batch_size)]
