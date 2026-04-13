from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from config import MA_PERIOD, TOUCH_THRESHOLD_PCT


@dataclass
class Event:
    ticker: str
    event_type: str       # CROSS_ABOVE | CROSS_BELOW | TOUCH_FROM_ABOVE | TOUCH_FROM_BELOW
    ma_period: int
    latest_close: float
    ma_value: float
    distance_pct: float   # signed: positive = close above MA
    timestamp: datetime


def scan_ticker(ticker: str, df: pd.DataFrame) -> list[Event]:
    """Analyse *df* for SMA-150 interaction events.

    Returns a list of Event objects (typically 0 or 1).
    No imports from alerter.py or main.py — fully self-contained.
    """
    if df is None or df.empty:
        return []

    df = df.copy()
    df["SMA"] = df["Close"].rolling(MA_PERIOD).mean()
    df = df.dropna(subset=["SMA"]).reset_index(drop=True)

    if len(df) < 2:
        return []

    latest_close = float(df["Close"].iloc[-1])
    latest_ma    = float(df["SMA"].iloc[-1])
    prev_close   = float(df["Close"].iloc[-2])
    prev_ma      = float(df["SMA"].iloc[-2])

    distance_pct = (latest_close - latest_ma) / latest_ma * 100
    now = datetime.now()
    events: list[Event] = []

    # --- Cross events (take priority over touch) ---
    if prev_close < prev_ma and latest_close > latest_ma:
        events.append(Event(
            ticker=ticker,
            event_type="CROSS_ABOVE",
            ma_period=MA_PERIOD,
            latest_close=latest_close,
            ma_value=latest_ma,
            distance_pct=distance_pct,
            timestamp=now,
        ))
        return events

    if prev_close > prev_ma and latest_close < latest_ma:
        events.append(Event(
            ticker=ticker,
            event_type="CROSS_BELOW",
            ma_period=MA_PERIOD,
            latest_close=latest_close,
            ma_value=latest_ma,
            distance_pct=distance_pct,
            timestamp=now,
        ))
        return events

    # --- Touch events (only when no cross occurred) ---
    within_threshold = abs(distance_pct) <= TOUCH_THRESHOLD_PCT

    if within_threshold and latest_close >= latest_ma:
        events.append(Event(
            ticker=ticker,
            event_type="TOUCH_FROM_ABOVE",
            ma_period=MA_PERIOD,
            latest_close=latest_close,
            ma_value=latest_ma,
            distance_pct=distance_pct,
            timestamp=now,
        ))

    elif within_threshold and latest_close <= latest_ma:
        events.append(Event(
            ticker=ticker,
            event_type="TOUCH_FROM_BELOW",
            ma_period=MA_PERIOD,
            latest_close=latest_close,
            ma_value=latest_ma,
            distance_pct=distance_pct,
            timestamp=now,
        ))

    return events
