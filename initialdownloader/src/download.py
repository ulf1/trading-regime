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
            
            if data.empty or 'Adj Close' not in data.columns:
                logger.warning(f"No data downloaded for {ticker}.")
                return pd.DataFrame()

            ticker_df = data[['Adj Close']].dropna().copy()
            if ticker_df.empty:
                return pd.DataFrame()
                
            ticker_df = ticker_df.tail(2000) # Keep only the last 2000 points
            
            ticker_df = ticker_df.reset_index()
            ticker_df['ticker'] = ticker
            ticker_df['Date'] = ticker_df['Date'].dt.strftime('%Y-%m-%d')
            ticker_df = ticker_df.rename(columns={'Date': 'date', 'Adj Close': 'adj_close'})
            
            if isinstance(ticker_df.columns, pd.MultiIndex):
                ticker_df.columns = [col[0] for col in ticker_df.columns]
                
            return ticker_df
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            if attempt < max_retries - 1:
                backoff_time = 2 ** attempt
                logger.info(f"Retrying in {backoff_time} seconds...")
                time.sleep(backoff_time)
            else:
                logger.error(f"Max retries exceeded for {ticker}.")
                
    return pd.DataFrame()
