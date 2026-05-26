import time
import logging
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

def download_missing_data(ticker: str, max_retries: int = 3) -> pd.DataFrame:
    """
    Downloads historical data for a ticker using yfinance with retry logic.
    Filters the latest 2000 points.
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Downloading data for {ticker}, attempt {attempt + 1}")
            data = yf.download([ticker], period="9y", interval="1d", auto_adjust=False, threads=False, progress=False)
            
            # Flatten MultiIndex columns immediately if present
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            if data.empty or 'Adj Close' not in data.columns:
                logger.warning(f"No data downloaded for {ticker}.")
                return pd.DataFrame()

            ticker_df = data[['Adj Close']].dropna().copy()
            if ticker_df.empty:
                return pd.DataFrame()
                
            ticker_df = ticker_df.tail(2000) # Keep only the last 2000 points
            
            # Directly extract dates from DatetimeIndex to avoid KeyError: 'Date'
            ticker_df['date'] = pd.to_datetime(ticker_df.index).strftime('%Y-%m-%d')
            ticker_df['ticker'] = ticker
            ticker_df = ticker_df.rename(columns={'Adj Close': 'adj_close'})
            return ticker_df[['date', 'ticker', 'adj_close']]
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            if attempt < max_retries - 1:
                backoff_time = 2 ** attempt
                logger.info(f"Retrying in {backoff_time} seconds...")
                time.sleep(backoff_time)
            else:
                logger.error(f"Max retries exceeded for {ticker}.")
                
    return pd.DataFrame()
