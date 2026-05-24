---
name: 327-pandas-unittest
description: >
  Best practices for writing unit tests for pandas code. Apply these rules
  whenever writing, reviewing, or debugging tests for pandas data transformations
  — including testing DataFrame and Series values, shapes, dtypes, missing values,
  boundary edge cases, MultiIndices, and mocking I/O operations.
tags:
  - python
  - pandas
  - unit-testing
  - pytest
  - mock
capabilities:
  actions:
    - assert_frame_equality
    - test_shape_and_dtype
    - mock_external_io
    - verify_missing_data
    - verify_index_integrity
    - test_idempotency
    - test_time_series_assertions
  file_extensions:
    - .py
    - .ipynb
triggers:
  verbs:
    - test
    - assert
    - verify
    - mock
    - validate
  nouns:
    - pytest
    - assert_frame_equal
    - assert_series_equal
    - assert_index_equal
    - tmp_path
    - patch
    - fixture
manifest:
  knowledge_base:
    - assets/unittest_metadata.json
    - assets/manifest.json
  logic_examples:
    - examples/test_pandas_pipeline.py
---

# Pandas Unit Testing Skill (Skill 327_unittest)

This skill details mandatory architecture for writing robust, maintainable, and high-performance unit tests for pandas data transformations using `pytest` and `pandas.testing`.

---

## 1. High-Performance Assertion Patterns
Strict isolation of **pure transformations**, **minimal inline fixtures**, and **assertion accuracy** is mandatory.

### Testing Best Practices Checklist
| Testing Requirement | Implementation Rule | Rationale |
| :--- | :--- | :--- |
| **Pure Functions** | Separate I/O operations from business transforms; test functions taking df in, df out | Bypasses slow network/disk bottlenecks during test runs |
| **No Manual loops** | Never check DataFrame values using plain Python iterations or row comparisons | 100x slower and prone to boundary glitches |
| **pd.testing Assertions**| Always use `pd.testing.assert_frame_equal` rather than `==` or `.equals()` | Plain comparisons raise ambiguous truth-value errors; `.equals()` ignores NaN alignments |
| **Small Fixtures** | Build tiny inline synthetic DataFrames instead of loading large sample files | Increases speed and makes test intent immediately explicit |
| **Mocking I/O** | Mock external APIs, database drivers, and file methods (`pd.read_csv`, etc.) | Ensures zero network or local disk dependency |
| **Index Gaps** | Assert indices are reset using `reset_index(drop=True)` after filtering | Gapped RangeIndices cause unexpected downstream lookup failures |

---

## 2. 🧩 Standard Assertions Guide

### Comparing DataFrames
For comparing full tabular datasets:

```python
import pandas as pd

# GOOD — fully checks shapes, values, dtypes, and indices
pd.testing.assert_frame_equal(result, expected)
```

Useful parameter flags in `assert_frame_equal`:
* `check_dtype=True`: Fails if numeric column types differ (e.g. float32 vs float64).
* `check_index_type=True`: Fails if index types differ (e.g. RangeIndex vs Int64Index).
* `check_like=True`: Ignores row and column ordering during the comparison.
* `rtol` & `atol`: Float precision tolerance parameters (default: `rtol=1e-5`, `atol=1e-8`).

### Comparing Series and Indices
Verify sub-components explicitly:

```python
# Verify individual series values and categories
pd.testing.assert_series_equal(result["status"], expected_series)

# Verify Index alignments
pd.testing.assert_index_equal(result.index, expected_index)
```

---

## 3. 🧪 Core Testing Paradigms

### A. Dtype and Shape Checks
Assert shape reductions and dtype conversions as core contract properties:

```python
def test_drops_invalid_rows():
    df = make_df(amount=[100, None, -5])
    result = clean_orders(df)
    
    assert result.shape == (1, 3), f"Expected shape (1, 3), got {result.shape}"
    assert result["amount"].dtype == "float32"
```

---

### B. Parametrization Over Input Bounds
Use `@pytest.mark.parametrize` to quickly run boundary value checks without repeating boilerplate:

```python
import pytest

@pytest.mark.parametrize("amount,expected_len", [
    ([100.0, 200.0], 2),    # all positive
    ([-10.0, 50.0],  1),    # negatives dropped
    ([None, None],   0),    # nulls dropped
])
def test_amount_filters(amount, expected_len):
    df = pd.DataFrame({"id": range(len(amount)), "amount": amount, "status": "active"})
    result = clean_orders(df)
    assert len(result) == expected_len
```

---

### C. Testing Idempotency
Ensure that running a clean or transforming operation twice returns the exact same DataFrame:

```python
def test_clean_is_idempotent(raw_data):
    once = clean_orders(raw_data)
    twice = clean_orders(once)
    pd.testing.assert_frame_equal(once, twice)
```

---

## 4. 🧪 Mocking & File system Sandbox
Never hit local databases or make remote calls in tests. Use standard `unittest.mock.patch` and pytest's `tmp_path`:

```python
from unittest.mock import patch

# Mock read_csv to prevent disk access
@patch("pandas.read_csv")
def test_data_loader(mock_read, raw_data):
    mock_read.return_value = raw_data
    result = load_data("fake_path.csv")
    
    mock_read.assert_called_once_with("fake_path.csv")
    assert len(result) == len(raw_data)
```

```python
# Use tmp_path to test physical file writing securely
def test_round_trip_parquet(raw_data, tmp_path):
    path = str(tmp_path / "sandbox.parquet")
    raw_data.to_parquet(path, index=False)
    
    reloaded = pd.read_parquet(path)
    pd.testing.assert_frame_equal(reloaded, raw_data)
```

---

## 5. Manifest & Logic Examples
Refer to the `assets/` and `examples/` directories for standardized configurations and comprehensive test suites:
* **Assets**: Refer to `assets/manifest.json` and `assets/unittest_metadata.json` for capabilities schemas and standard mock configurations.
* **Logic Example**: Refer to `examples/test_pandas_pipeline.py` for a production-ready pytest file demonstrating:
  - Clean `pd.testing.assert_frame_equal` integrations.
  - Verification of shapes, dtypes, and null counts.
  - Isolated parameter evaluations.
  - Boundary checks (empty inputs, single rows).
  - Validation of no in-place parameter mutations.
  - Zero disk-footprint testing via mocked readers.
