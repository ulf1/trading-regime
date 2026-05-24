import sys
import os
import pandas as pd

# Add src to python path to import modules cleanly during tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from scraper import is_valid_equity_ticker, fetch_historical_data

def test_is_valid_equity_ticker():
    # Valid Equities
    assert is_valid_equity_ticker("AAPL") is True
    assert is_valid_equity_ticker("NZM2.HM") is True
    assert is_valid_equity_ticker("ISCTR.IS") is True
    assert is_valid_equity_ticker("YKBNK.IS") is True

    # Oslo Professional Segment Bonds
    assert is_valid_equity_ticker("SB1NO47-PRO.OL") is False
    assert is_valid_equity_ticker("EVINY13-PRO-ESG.OL") is False
    assert is_valid_equity_ticker("SPOL45-PRO.OL") is False

    # Warrants, Preferred Stocks, Units, and Futures
    assert is_valid_equity_ticker("AAPL-W") is False
    assert is_valid_equity_ticker("AAPL.WS") is False
    assert is_valid_equity_ticker("SPY-P") is False
    assert is_valid_equity_ticker("SEC-U") is False
    assert is_valid_equity_ticker("ES=F") is False

    # General digit-and-hyphen structured debt patterns
    assert is_valid_equity_ticker("NOR22-1234.OL") is False
    assert is_valid_equity_ticker("BOND-12.OL") is False

def test_fetch_historical_data_skips_invalid():
    df = fetch_historical_data("SB1NO47-PRO.OL")
    assert df.empty is True
    
    df_warrant = fetch_historical_data("AAPL-W")
    assert df_warrant.empty is True
