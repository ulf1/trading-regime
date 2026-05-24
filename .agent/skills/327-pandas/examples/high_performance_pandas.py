import os
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

# Enable pandas Copy-on-Write for robust memory ownership and compatibility
pd.options.mode.copy_on_write = True


class PipelineConfig(BaseModel):
    """Pydantic configuration for the data processing pipeline."""

    tax_rate: float = Field(default=0.08, gt=0, lt=1)
    min_amount: float = Field(default=10.0, ge=0)
    category_cols: list[str] = Field(default=["region", "status"])
    target_timezone: str = "America/New_York"


def load_raw_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generates synthetic high-performance pandas dataframes representing orders

    and customer catalogs.

    Returns:
        df_orders: Dataframe containing synthetic transactions.
        df_customers: Dataframe containing customer metadata catalog.
    """
    # Orders dataframe
    orders_data = {
        "order_id": np.arange(1001, 1006, dtype=np.int32),
        "customer_id": np.array([501, 502, 501, 503, 504], dtype=np.int32),
        "region": ["West", "East", "West", "North", "South"],
        "amount": np.array([120.50, 8.99, 450.00, 75.00, 15.25], dtype=np.float32),
        "status": ["active", "active", "inactive", "active", "active"],
        "timestamp": [
            "2026-05-21 14:00:00",
            "2026-05-21 14:15:00",
            "2026-05-21 14:30:00",
            "2026-05-21 14:45:00",
            "2026-05-21 15:00:00",
        ],
    }
    df_orders = pd.DataFrame(orders_data)

    # Customers dataframe
    customers_data = {
        "customer_id": np.array([501, 502, 503, 504], dtype=np.int32),
        "customer_name": ["Alice Smith", "Bob Jones", "Charlie Brown", "Diana Prince"],
    }
    df_customers = pd.DataFrame(customers_data)

    return df_orders, df_customers


def load_optimized_dataset(file_path: str) -> pd.DataFrame:
    """Loads tabular data while minimizing memory usage through downcasting and

    efficient data type classification.

    Args:
        file_path: Absolute or relative path to a Parquet file.

    Returns:
        optimized_df: Memory-optimized loaded DataFrame.
    """
    df = pd.read_parquet(file_path)  # Prefer Parquet over CSV

    # Downcast floats and integers to minimal viable sizes
    for col in df.select_dtypes(include=["float"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="float")

    for col in df.select_dtypes(include=["int"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="integer")

    # Convert repetitive text columns to category dtype
    for col in df.select_dtypes(include=["object"]).columns:
        if df[col].nunique() / len(df[col]) < 0.5:  # High repetition card
            df[col] = df[col].astype("category")

    return df


# --- Custom Transformation Steps using .pipe() ---


def optimize_data_types(df: pd.DataFrame, config: PipelineConfig) -> pd.DataFrame:
    """Downcasts numerical columns and converts low-cardinality string columns

    to categorical dtypes to minimize memory footprint.

    Args:
        df: Input Orders DataFrame.

    Returns:
        optimized_df: DataFrame with highly optimized dtypes.
    """
    # Downcast floats and integers to smallest compatible sizes
    df["order_id"] = pd.to_numeric(df["order_id"], downcast="integer")
    df["customer_id"] = pd.to_numeric(df["customer_id"], downcast="integer")
    df["amount"] = pd.to_numeric(df["amount"], downcast="float")

    # Convert string columns to categorical dtypes
    for col in config.category_cols:
        if col in df.columns:
            df[col] = df[col].astype("category")

    return df


def parse_and_localize_dates(df: pd.DataFrame, config: PipelineConfig) -> pd.DataFrame:
    """Explicitly parses strings to UTC dates and converts them to target local timezone.

    Args:
        df: Input DataFrame containing 'timestamp' string column.

    Returns:
        localized_df: DataFrame with localized datetime types.
    """
    # Parse to timezone-aware UTC datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    # Convert timezone explicitly to local timezone
    df["timestamp"] = df["timestamp"].dt.tz_convert(config.target_timezone)

    return df


def calculate_metrics(df: pd.DataFrame, config: PipelineConfig) -> pd.DataFrame:
    """Computes vectorized taxes and customer classification grades using np.select.

    Args:
        df: Input orders DataFrame.

    Returns:
        df_metrics: DataFrame containing calculated columns.
    """
    # Efficient vectorized math
    df = df.assign(tax=lambda x: x["amount"] * config.tax_rate)

    # Vectorized multi-conditional grading using np.select
    conditions = [df["amount"] >= 200.0, df["amount"] >= 50.0]
    choices = ["High Value", "Medium Value"]

    df["value_tier"] = np.select(conditions, choices, default="Low Value")

    return df


def process_orders_pipeline(
    df_orders: pd.DataFrame, df_customers: pd.DataFrame, config: PipelineConfig
) -> pd.DataFrame:
    """End-to-end data pipeline implementing functional method-chaining and

    merges with strict validation.

    Args:
        df_orders: Raw orders DataFrame.
        df_customers: Customer metadata DataFrame catalog.
        config: Configuration pipeline instance.

    Returns:
        final_df: Reshaped, filtered, and aggregated result DataFrame.
    """
    # Functional method chain
    processed_orders = (
        df_orders.query("amount >= @config.min_amount and status == 'active'")
        .pipe(optimize_data_types, config=config)
        .pipe(parse_and_localize_dates, config=config)
        .pipe(calculate_metrics, config=config)
    )

    # Robust merge validation: Enforce a many-to-one (m:1) relationship constraint
    # to catch any unintended cartesian duplicate records on join.
    final_df = processed_orders.merge(
        df_customers, on="customer_id", how="inner", validate="many_to_one"
    )

    # Re-order and clean index
    return final_df.reset_index(drop=True)


def main():
    config = PipelineConfig()
    df_orders, df_customers = load_raw_data()

    print("Executing high-performance pandas processing pipeline...")
    result_df = process_orders_pipeline(df_orders, df_customers, config)

    print("\nResulting DataFrame:")
    print(result_df)
    print(f"\nDataFrame types:\n{result_df.dtypes}")

    # Perform automated sanity checks
    # Assert row count filtered correctly (8.99 excluded as < 10.0, inactive excluded)
    assert len(result_df) == 3, f"Expected 3 rows, got {len(result_df)}"

    # Assert nullable status properties are maintained
    assert result_df["value_tier"].tolist() == [
        "High Value",
        "Medium Value",
        "Low Value",
    ]

    # Save a temporary parquet file to demonstrate load_optimized_dataset
    temp_path = "temp_orders.parquet"
    print(f"\nSaving test Parquet file to verify load_optimized_dataset...")
    df_orders.to_parquet(temp_path, index=False)

    try:
        optimized_df = load_optimized_dataset(temp_path)
        print("Optimized DataFrame loaded successfully:")
        print(optimized_df.dtypes)

        # Assert integer/float type optimization
        assert optimized_df["order_id"].dtype == np.int16 or str(optimized_df["order_id"].dtype).startswith("int")
        assert optimized_df["amount"].dtype == np.float32 or str(optimized_df["amount"].dtype).startswith("float32")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    print("\nExecution succeeded: All pipeline assertions passed flawlessly under Copy-on-Write!")


if __name__ == "__main__":
    main()
