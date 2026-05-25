import pytest
import pandas as pd
import numpy as np
from dataset import prepare_training_data


def test_prepare_training_data_success():
    # Construct mock raw prices data
    data = [
        {"ticker": "AAPL", "date": "2026-05-01", "adj_close": 100.0},
        {"ticker": "AAPL", "date": "2026-05-02", "adj_close": 102.0},
        {"ticker": "AAPL", "date": "2026-05-03", "adj_close": 101.0},
        {"ticker": "MSFT", "date": "2026-05-01", "adj_close": 200.0},
        {"ticker": "MSFT", "date": "2026-05-02", "adj_close": 204.0},
        # Introduce a missing entry for MSFT on 2026-05-03 to test fill/impute
    ]
    df_raw = pd.DataFrame(data)
    
    df_returns, df_prices = prepare_training_data(df_raw)
    
    # 1. Output shapes
    # 3 unique dates total: 2026-05-01, 2026-05-02, 2026-05-03
    # 2 unique tickers: AAPL, MSFT
    assert df_prices.shape == (3, 2)
    
    # Returns should have T-1 rows (first row diff dropped)
    assert df_returns.shape == (2, 2)
    
    # 2. Ascending chronological sorting check
    assert df_prices.index.tolist() == ["2026-05-01", "2026-05-02", "2026-05-03"]
    assert df_returns.index.tolist() == ["2026-05-02", "2026-05-03"]
    
    # 3. Log returns calculation check for AAPL:
    # 2026-05-02 return: log(102) - log(100) = log(1.02)
    expected_ret_aapl = np.log(102.0) - np.log(100.0)
    np.testing.assert_allclose(df_returns.loc["2026-05-02", "AAPL"], expected_ret_aapl)
    
    # 4. Imputation and boundary propagation check:
    # MSFT had missing price on 2026-05-03. bfill/ffill should carry 204.0 forward.
    # Therefore, MSFT price on 2026-05-03 should be 204.0.
    assert df_prices.loc["2026-05-03", "MSFT"] == 204.0
    # The return on 2026-05-03 for MSFT should be log(204) - log(204) = 0.0
    assert df_returns.loc["2026-05-03", "MSFT"] == 0.0

def test_prepare_training_data_empty():
    df_empty = pd.DataFrame(columns=["ticker", "date", "adj_close"])
    with pytest.raises(ValueError, match="Input DataFrame is empty"):
        prepare_training_data(df_empty)
