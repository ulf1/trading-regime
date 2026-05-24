from unittest.mock import patch
import numpy as np
import pandas as pd
import pytest


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """ETL Pure transformation: cleans transactions data by filtering out negative

    values, casting status to category, and handling missing ids.

    Args:
        df: Input DataFrame representing raw transaction records.

    Returns:
        clean_df: Cleaned transaction DataFrame.
    """
    if df.empty:
        return pd.DataFrame(columns=["transaction_id", "amount", "status"])

    # Drop rows missing transaction ID
    df_clean = df.dropna(subset=["transaction_id"])

    # Filter out non-positive transactions and cast types explicitly
    df_clean = df_clean.query("amount > 0").assign(
        transaction_id=lambda x: x["transaction_id"].astype(np.int32),
        amount=lambda x: x["amount"].astype(np.float32),
        status=lambda x: x["status"].astype("category"),
    )

    # Re-order and reset index cleanly to prevent RangeIndex gaps
    return df_clean.reset_index(drop=True)


# --- Pytest Test Suite ---


class TestCleanTransactionsPipeline:
    """Robust test suite verifying correctness, schema integrity, and boundary

    behaviors of clean_transactions.
    """

    @pytest.fixture
    def raw_transactions(self) -> pd.DataFrame:
        """Fixture representing raw orders metadata with edge case noise."""
        return pd.DataFrame(
            {
                "transaction_id": [101, 102, None, 104, 105],
                "amount": [55.50, -10.00, 150.00, 300.00, 5.00],
                "status": ["active", "active", "inactive", "active", "inactive"],
            }
        )

    def test_correct_filtering_and_conversion(self, raw_transactions):
        """Verify valid rows are cleaned, formatted, and converted properly."""
        result = clean_transactions(raw_transactions)

        # Build expected DataFrame explicitly (note: row order and category types must match)
        expected = pd.DataFrame(
            {
                "transaction_id": np.array([101, 104, 105], dtype=np.int32),
                "amount": np.array([55.50, 300.00, 5.00], dtype=np.float32),
                "status": pd.Series(["active", "active", "inactive"], dtype="category"),
            }
        )

        # Assert full equality (types, category categories, indices)
        pd.testing.assert_frame_equal(
            result,
            expected,
            check_dtype=True,
            check_index_type=True,
            err_msg="Cleaned transaction DataFrame mismatch.",
        )

    def test_shapes_and_dtypes(self, raw_transactions):
        """Assert output shape drops invalid rows and maintains exact target dtypes."""
        result = clean_transactions(raw_transactions)

        # Expected size: drops row 1 (negative amount) and row 2 (null ID) -> 3 rows remaining
        assert result.shape == (3, 3)
        assert result["transaction_id"].dtype == np.int32
        assert result["amount"].dtype == np.float32
        assert result["status"].dtype.name == "category"

    def test_no_input_mutation(self, raw_transactions):
        """Verify the input DataFrame remains unaltered (no side-effects)."""
        backup_df = raw_transactions.copy()

        _ = clean_transactions(raw_transactions)

        pd.testing.assert_frame_equal(
            raw_transactions,
            backup_df,
            err_msg="Transformation function mutated input parameters!",
        )

    @pytest.mark.parametrize(
        "amounts,expected_count",
        [
            ([100.0, 200.0, 300.0], 3),  # All valid positive
            ([-5.0, 0.0, 120.0], 1),  # Filter out negative and zero values
            ([np.nan, 50.0], 1),  # NaN values are filtered by the query
        ],
    )
    def test_parametrized_amount_bounds(self, amounts, expected_count):
        """Enforce strict value range filtering on different numeric values."""
        df = pd.DataFrame(
            {
                "transaction_id": range(len(amounts)),
                "amount": amounts,
                "status": "active",
            }
        )
        result = clean_transactions(df)
        assert len(result) == expected_count

    def test_empty_dataframe(self):
        """Sanity check empty DataFrames keep schema structure intact."""
        empty_input = pd.DataFrame(columns=["transaction_id", "amount", "status"])
        result = clean_transactions(empty_input)

        assert result.empty
        assert list(result.columns) == ["transaction_id", "amount", "status"]

    def test_single_valid_row(self):
        """Verify behavior with single-row datasets."""
        single_row = pd.DataFrame(
            {"transaction_id": [1], "amount": [12.0], "status": ["active"]}
        )
        result = clean_transactions(single_row)
        assert len(result) == 1
        assert result.loc[0, "transaction_id"] == 1

    @patch("pandas.read_csv")
    def test_mocked_io_reads(self, mock_read_csv, raw_transactions):
        """Demonstrate zero-disk footprint testing by mocking standard I/O reads."""
        mock_read_csv.return_value = raw_transactions

        # Executing loader step with mocked response
        loaded_df = pd.read_csv("fake_path.csv")
        result = clean_transactions(loaded_df)

        mock_read_csv.assert_called_once_with("fake_path.csv")
        assert len(result) == 3
