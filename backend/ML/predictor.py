import pandas as pd
from datetime import datetime, timedelta
import statistics

def forecast_from_history(history_records: list, horizon_hours: int = 12, step_minutes: int = 60):
    if not history_records:
        # fallback demo
        now = datetime.utcnow()
        return [
            {"time": (now + timedelta(minutes=step_minutes*i)).isoformat(),
             "taken_spots": 130 + i*5,
             "estimated_total": 200}
            for i in range(horizon_hours)
        ]

    df = pd.DataFrame(history_records)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    # simple moving average on taken_spots
    window = max(1, min(5, len(df)))
    taken_ma = int(df["taken_spots"].tail(window).mean())

    # pick a stable total (median of past totals)
    est_total = int(statistics.median([max(1, t) for t in df["estimated_total"].tolist()]))

    start = df["timestamp"].iloc[-1]
    horizon = []
    for i in range(1, horizon_hours + 1):
        ts = start + timedelta(minutes=step_minutes * i)
        horizon.append({
            "time": ts.isoformat(),
            "taken_spots": taken_ma,          # flat MA; improve later if time permits
            "estimated_total": est_total
        })
    return horizon
