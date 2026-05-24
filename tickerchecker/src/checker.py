import logging
import yfinance as yf
import pandas as pd

logger = logging.getLogger(__name__)

def check_stale_ticker(ticker: str) -> tuple[bool, pd.DataFrame]:
    """
    Checks if a ticker has data on yfinance over the last 3 weeks.
    Returns a boolean (is_alive) and a DataFrame of the downloaded data.
    """
    logger.info(f"Checking stale ticker {ticker}...")
    try:
        data = yf.download([ticker], period="3wk", interval="1d", auto_adjust=False, threads=False, progress=False)
        
        if data.empty or 'Adj Close' not in data.columns:
            logger.warning(f"Ticker {ticker} appears to be dead (no data found).")
            return False, pd.DataFrame()
            
        ticker_df = data[['Adj Close']].dropna().copy()
        if ticker_df.empty:
            logger.warning(f"Ticker {ticker} appears to be dead (all NaNs).")
            return False, pd.DataFrame()
            
        ticker_df = ticker_df.reset_index()
        ticker_df['ticker'] = ticker
        ticker_df['Date'] = ticker_df['Date'].dt.strftime('%Y-%m-%d')
        ticker_df = ticker_df.rename(columns={'Date': 'date', 'Adj Close': 'adj_close'})
        
        # Unpack MultiIndex columns if necessary
        if isinstance(ticker_df.columns, pd.MultiIndex):
            ticker_df.columns = [col[0] for col in ticker_df.columns]
            
        return True, ticker_df
    except Exception as e:
        logger.error(f"Error checking ticker {ticker}: {e}")
        return False, pd.DataFrame()
