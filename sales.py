import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

from ml_anomalies import flag_anomalies

load_dotenv()

DB_PASSWORD = os.getenv("PASSWORD")
ROOT = Path(__file__).resolve().parent
RAW_FILE = ROOT / "data" / "product_sales_dataset_final.csv"

TEXT_COLUMNS = [
    "customer_name", "city", "state", "region", "country",
    "category", "sub_category", "product_name",
]
NUMBER_COLUMNS = ["quantity", "unit_price", "revenue", "profit"]
REQUIRED_COLUMNS = [
    "order_id", "order_date", "customer_name", "product_name",
    "quantity", "unit_price", "revenue",
]



def clean_column_name(name):
    # "Order Date" -> "order_date"
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def extract():
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"{RAW_FILE} not found")

    try:
        df = pd.read_csv(RAW_FILE)
    except pd.errors.EmptyDataError:
        raise ValueError("sales CSV is empty")
    except pd.errors.ParserError:
        raise ValueError("couldn't parse the sales CSV")

    df.columns = [clean_column_name(col) for col in df.columns]
    return df


def transform(df):
    df = df.copy()

    df["order_id"] = pd.to_numeric(df["order_id"], errors="coerce").astype("Int64")
    df["order_date"] = pd.to_datetime(df["order_date"], format="%m-%d-%y", errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype("Int64")

    for col in ["unit_price", "revenue", "profit"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in TEXT_COLUMNS:
        df[col] = df[col].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)

    df = df.drop_duplicates()
    df = df.dropna(subset=REQUIRED_COLUMNS)  # these fields are non-negotiable, drop the row if any are missing
    df[TEXT_COLUMNS] = df[TEXT_COLUMNS].fillna("Unknown")
    df[NUMBER_COLUMNS] = df[NUMBER_COLUMNS].fillna(df[NUMBER_COLUMNS].median())

    df["order_year"] = df["order_date"].dt.year
    df["order_month"] = df["order_date"].dt.month
    df["profit_margin"] = np.where(df["revenue"] > 0, df["profit"] / df["revenue"], np.nan)

    return flag_anomalies(df)


def load_to_postgresql(df):
    df = df.drop_duplicates(subset=["order_id"], keep="first")

    engine = create_engine(f"postgresql://postgres:{DB_PASSWORD}@localhost:5432/Sales")
    table_name = "Sales Orders"

    try:
        existing = pd.read_sql_table(table_name, engine)
        df = pd.concat([existing, df], ignore_index=True)
        df = df.drop_duplicates(subset=["order_id"], keep="first")
    except ValueError:
        pass  # first run, table doesn't exist yet

    # rows pulled back from postgres could still be carrying the old column
    df.to_sql(table_name, engine, if_exists="replace", index=False)
    return df


def etl():
    raw = extract()
    clean = transform(raw)
    loaded = load_to_postgresql(clean)
    print(f"Anomalies flagged: {int(clean['is_anomaly'].sum())}")
    return loaded



if __name__ == "__main__":
    etl()