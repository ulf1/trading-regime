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
        
        # Flatten MultiIndex columns immediately if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        if data.empty or 'Adj Close' not in data.columns:
            logger.warning(f"Ticker {ticker} appears to be dead (no data found).")
            return False, pd.DataFrame()
            
        ticker_df = data[['Adj Close']].dropna().copy()
        if ticker_df.empty:
            logger.warning(f"Ticker {ticker} appears to be dead (all NaNs).")
            return False, pd.DataFrame()
            
        # Directly extract dates from DatetimeIndex to avoid KeyError: 'Date'
        ticker_df['date'] = pd.to_datetime(ticker_df.index).strftime('%Y-%m-%d')
        ticker_df['ticker'] = ticker
        ticker_df = ticker_df.rename(columns={'Adj Close': 'adj_close'})
        return True, ticker_df[['date', 'ticker', 'adj_close']]
    except Exception as e:
        logger.error(f"Error checking ticker {ticker}: {e}")
        return False, pd.DataFrame()
