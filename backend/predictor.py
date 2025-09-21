import pandas as pd
import numpy as np
import statistics
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor


def train_random_forest(df: pd.DataFrame):
    """
    Train a Random Forest Regressor on time-based features (day/hour cycles).
    Returns the trained model, estimated_total, and the last timestamp.
    """

    # Extract features
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["hour"] = df["timestamp"].dt.hour

    # Cyclical encoding
    df["day_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["day_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

    X = df[["day_sin", "day_cos", "hour_sin", "hour_cos"]]
    y = df["taken_spots"]

    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X, y)

    # Pick a stable "total spots" estimate
    est_total = int(statistics.median([max(1, t) for t in df["estimated_total"].tolist()]))

    return model, est_total, df["timestamp"].iloc[-1]


def forecast_from_history(history_records: list, horizon_hours: int = 12, step_minutes: int = 60):
    """
    Forecast parking occupancy using:
    - Random Forest (if enough historical data is available)
    - Moving average fallback (if dataset is tiny)
    """

    if not history_records:
        # No data at all: demo output
        now = datetime.utcnow()
        return [
            {"time": (now + timedelta(minutes=step_minutes * i)).isoformat(),
             "taken_spots": 130 + i * 5,
             "estimated_total": 200}
            for i in range(horizon_hours)
        ]

    # Convert history to DataFrame
    df = pd.DataFrame(history_records)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    # If we don’t have enough records → fallback to moving average
    if len(df) < 20:  # tweak threshold as you like
        window = max(1, min(5, len(df)))
        taken_ma = int(df["taken_spots"].tail(window).mean())
        est_total = int(statistics.median([max(1, t) for t in df["estimated_total"].tolist()]))
        start = df["timestamp"].iloc[-1]

        horizon = []
        for i in range(1, horizon_hours + 1):
            ts = start + timedelta(minutes=step_minutes * i)
            horizon.append({
                "time": ts.isoformat(),
                "taken_spots": taken_ma,  # flat line forecast
                "estimated_total": est_total
            })
        return horizon

    # Otherwise → train Random Forest
    model, est_total, last_ts = train_random_forest(df)

    horizon = []
    for i in range(1, horizon_hours + 1):
        ts = last_ts + timedelta(minutes=step_minutes * i)

        # Features for prediction
        day = ts.dayofweek
        hour = ts.hour
        features = {
            "day_sin": np.sin(2 * np.pi * day / 7),
            "day_cos": np.cos(2 * np.pi * day / 7),
            "hour_sin": np.sin(2 * np.pi * hour / 24),
            "hour_cos": np.cos(2 * np.pi * hour / 24),
        }

        taken_pred = int(model.predict([list(features.values())])[0])

        horizon.append({
            "time": ts.isoformat(),
            "taken_spots": taken_pred,
            "estimated_total": est_total
        })

    return horizon
