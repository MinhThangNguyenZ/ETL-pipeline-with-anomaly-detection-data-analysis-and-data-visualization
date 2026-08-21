# ETL Pipeline with Anomaly Detection, Data Analysis & Visualization

An end-to-end ETL pipeline that ingests raw product sales data, cleans and transforms it, flags anomalous orders using machine learning, and loads the result into PostgreSQL for downstream analysis in Power BI.

## Overview

This project simulates a real-world sales data pipeline:

1. **Ingest** — pull the raw dataset from Kaggle
2. **Extract** — read and standardize the raw CSV
3. **Transform** — clean, type-cast, deduplicate, and engineer features
4. **Detect** — flag anomalous orders with an Isolation Forest model
5. **Load** — upsert the cleaned, scored data into PostgreSQL
6. **Visualize** — explore trends and flagged anomalies in a Power BI dashboard

## Tech Stack

- **Python** — pandas, NumPy, scikit-learn, SQLAlchemy
- **PostgreSQL** — storage for the cleaned, scored dataset
- **Power BI** — dashboard and reporting layer
- **Kaggle API** — dataset ingestion

## Project Structure

```
.
├── ingest.ipynb          # Pulls the raw dataset from Kaggle into ./data
├── sales.py              # Main ETL script: extract, transform, load
├── ml_anomalies.py       # Isolation Forest anomaly detection
├── data/                 # Raw dataset (not tracked in git)
├── .env.example          # Template for required environment variables
└── .gitignore
```

## Anomaly Detection Approach

`ml_anomalies.py` uses an **Isolation Forest** over a set of engineered features rather than raw values:

- Log-transformed quantity, unit price, revenue, and profit, so a handful of very large orders don't dominate the distance calculations
- A **revenue mismatch** feature comparing actual revenue to `quantity × unit_price`, since a large gap between the two is itself a signal of bad data or fraud
- Profit margin as an additional signal
- Anomaly scores are normalized against the 1st/99th percentile of the raw scores, so results stay on a stable 0–1 scale instead of being skewed by a few extreme outliers

The contamination rate (expected proportion of anomalies) is configurable via the `ANOMALY_CONTAMINATION` environment variable, defaulting to 1%.

## Setup

1. Clone the repo and install dependencies:
   ```bash
   pip install pandas numpy scikit-learn sqlalchemy python-dotenv kaggle psycopg2-binary
   ```
2. Copy `.env.example` to `.env` and fill in your PostgreSQL password:
   ```bash
   cp .env.example .env
   ```
3. Set up your Kaggle API credentials (`~/.kaggle/kaggle.json`) and run `ingest.ipynb` to download the dataset.
4. Run the pipeline:
   ```bash
   python sales.py
   ```

## Data Source

[Product Sales Dataset 2023–2024](https://www.kaggle.com/datasets/yashyennewar/product-sales-dataset-2023-2024) via Kaggle.

## Dashboard

Cleaned and scored data is loaded into PostgreSQL and visualized in a Power BI dashboard covering sales trends, regional performance, and flagged anomalies.
