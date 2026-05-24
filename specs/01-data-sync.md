
# Objective
Implement a daily market data synchronization pipeline that runs as a GCP Cloud Run Job. It fetches adjusted close prices for 1200 tickers via `yfinance` and stores them in a SQLite database backed by Google Cloud Storage.

# Architecture & Constraints
- **Execution:** GCP Cloud Run Job triggered daily by Cloud Scheduler.
- **Storage:** "Stateless" execution. The script MUST download `prices.db` from a GCS bucket at startup, perform database updates locally, and upload the updated `prices.db` back to GCS upon completion. Do NOT use persistent volumes.
- **Tech Stack:** Python 3.12. Strictly utilize `uv` (Skill 301) for dependency management and Docker caching. Do not use `requirements.txt`. Required libraries: `yfinance`, `pandas`, `google-cloud-storage`.

# Implementation Requirements

## 1. Database Schema (`datasync/database.py`)
- Define a single SQLite schema for a `prices` table: `ticker (TEXT)`, `date (DATE)`, `adj_close (REAL)`. Primary Key is `(ticker, date)`.
- **Do not create a `sync_state` table.** Instead, write a helper SQL query to derive the latest sync date dynamically (Hint: Use `SELECT ticker, MAX(date) AS last_sync FROM prices GROUP BY ticker;`).
- Write a robust upsert function to handle Pandas DataFrames being inserted into SQLite to avoid duplicate primary key errors.

## 2. Sync Logic (`datasync/sync.py`)
- Read a list of 1200 tickers from a GCS-hosted `tickers.csv` (or default to a hardcoded list for testing).
- Process tickers in batches of 200.
- For each batch, download the last 10 days of data (`period="10d", interval="1d"`) using `yfinance` to account for weekends/holidays.
- Extract only the "Adj Close" column, reshape the dataframe, and upsert into the SQLite `prices` table.
- Implement a retry mechanism with exponential backoff for `yfinance` network calls.

## 3. Storage & Orchestration (`datasync/main.py`)
- Use the `google-cloud-storage` client to handle the download and upload of `prices.db`.
- Implement standard Python `logging` (INFO level) instead of print statements to ensure GCP Cloud Logging captures execution metrics (rows updated, time taken, errors).
- Run `VACUUM` on the SQLite database before the final GCS upload to optimize storage size.

## 4. Containerization (`Dockerfile`)
- Create a multi-stage Dockerfile optimized for `uv` (as per Skill 301) to install dependencies rapidly and securely without relying on `requirements.txt`.

Please implement the Python application code, the Dockerfile, and provide the Terraform code (using the `340-terraform` skill) required to deploy the GCS Bucket, Cloud Run Job, and Cloud Scheduler.
