import os

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

NUMBER_COLUMNS = ["quantity", "unit_price", "revenue", "profit"]
CONTAMINATION = float(os.getenv("ANOMALY_CONTAMINATION", "0.01"))


def flag_anomalies(df):
    if not 0 < CONTAMINATION <= 0.5:
        raise ValueError("ANOMALY_CONTAMINATION must be between 0 and 0.5")

    df = df.copy()
    df["anomaly_score"] = 0.0
    df["is_anomaly"] = False

    if len(df) < 2:
        return df

    features, revenue_mismatch = build_features(df)
    scaled = RobustScaler().fit_transform(features)

    model = IsolationForest(
        n_estimators=100,
        max_samples=min(2048, len(df)),
        contamination=CONTAMINATION,
        n_jobs=-1,
        random_state=42,
    )
    labels = model.fit_predict(scaled)
    scores = -model.score_samples(scaled)  # flip the sign so higher = weirder

    df["anomaly_score"] = normalize_scores(scores)
    df["is_anomaly"] = labels == -1

    return df


def build_features(df):
    numbers = df[NUMBER_COLUMNS].astype(float).replace([np.inf, -np.inf], np.nan)
    numbers = numbers.fillna(numbers.median()).fillna(0)

    # revenue should roughly equal quantity * unit_price - a big gap is suspicious
    expected_revenue = numbers["quantity"] * numbers["unit_price"]
    scale = expected_revenue.abs().clip(lower=1.0)
    revenue_mismatch = ((numbers["revenue"] - expected_revenue) / scale).clip(-10, 10)

    profit_margin = np.where(
        numbers["revenue"].abs() > 1e-9,
        numbers["profit"] / numbers["revenue"],
        0.0,
    )

    # log1p so the handful of huge orders don't completely dominate the distances
    features = pd.DataFrame({
        "quantity": np.log1p(numbers["quantity"].clip(lower=0)),
        "unit_price": np.log1p(numbers["unit_price"].clip(lower=0)),
        "revenue": np.sign(numbers["revenue"]) * np.log1p(numbers["revenue"].abs()),
        "profit": np.sign(numbers["profit"]) * np.log1p(numbers["profit"].abs()),
        "profit_margin": np.clip(profit_margin, -10, 10),
        "revenue_mismatch": revenue_mismatch,
    }, index=df.index)

    return features.replace([np.inf, -np.inf], 0).fillna(0), revenue_mismatch


def normalize_scores(scores):
    # squash into 0-1 using percentiles so a few extreme outliers don't wreck the scale
    low, high = np.percentile(scores, [1, 99])
    if high <= low:
        return np.zeros_like(scores, dtype=float)
    return np.clip((scores - low) / (high - low), 0, 1)