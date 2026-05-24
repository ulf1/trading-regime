import pandas as pd
from src.sync import split_into_batches

def test_split_into_batches():
    tickers = ["T1", "T2", "T3", "T4", "T5"]
    batches = split_into_batches(tickers, batch_size=2)
    assert len(batches) == 3
    assert batches[0] == ["T1", "T2"]
    assert batches[1] == ["T3", "T4"]
    assert batches[2] == ["T5"]
