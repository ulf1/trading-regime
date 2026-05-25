import pandas as pd
import numpy as np

# Enable Copy-on-Write for future compatibility and memory efficiency on older pandas < 3.0
if pd.__version__.startswith("2."):
    pd.options.mode.copy_on_write = True


def prepare_training_data(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Preprocesses raw prices data into log returns.
    
    Processing steps:
      1. Pivots the DataFrame to get dates as rows and tickers as columns.
      2. Sorts the index chronologically from oldest to newest.
      3. Calculates log returns: log(p_t) - log(p_{t-1}).
      4. Imputes missing/NaN values with 0.0.
      
    Args:
        df_raw: DataFrame with columns ['ticker', 'date', 'adj_close']
        
    Returns:
        df_returns: DataFrame of log returns with shape (T-1, N).
        df_prices: Pivoted prices DataFrame with shape (T, N).
    """
    if df_raw.empty:
        raise ValueError("Input DataFrame is empty")

    # Pivot table: rows = date, columns = ticker, values = adj_close
    df_pivot = df_raw.pivot(index="date", columns="ticker", values="adj_close")
    
    # Sort index chronologically
    df_pivot = df_pivot.sort_index(ascending=True)
    
    # Fill any completely missing start/end prices at boundary via forward-fill/backward-fill
    # to avoid NaNs propagating through np.log
    df_pivot = df_pivot.ffill().bfill()
    
    # Calculate log returns: log(p_t) - log(p_{t-1})
    # Since diff() drops the first row (index 0 is NaN), we do diff() then drop the first row.
    df_log = np.log(df_pivot)
    df_returns = df_log.diff().iloc[1:]
    
    # Impute remaining missing values with 0.0 (e.g. if some asset had unchanged price or flat returns)
    df_returns = df_returns.fillna(0.0)
    
    return df_returns, df_pivot
