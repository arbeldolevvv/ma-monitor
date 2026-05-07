from dataclasses import dataclass
from datetime import datetime

import pandas as pd


@dataclass
class BearishEvent:
    ticker: str
    streak: int          # number of consecutive red candles
    latest_close: float
    timestamp: datetime


def scan_bearish(ticker: str, df: pd.DataFrame) -> list[BearishEvent]:
    """Return [BearishEvent] if the stock has 6+ consecutive red candles
    ending on the most recent trading day.

    A red candle is defined as Close < Open.
    Looks back at the last 10 candles maximum.

    No imports from alerter.py or main.py — fully self-contained.
    Importable as: from bearish_scanner import scan_bearish, BearishEvent
    """
    if df is None or df.empty:
        return []

    required_cols = {"Open", "Close"}
    if not required_cols.issubset(df.columns):
        return []

    candles = df.tail(10).reset_index(drop=True)
    if len(candles) < 1:
        return []

    streak = 0
    for i in range(len(candles) - 1, -1, -1):
        if float(candles["Close"].iloc[i]) < float(candles["Open"].iloc[i]):
            streak += 1
        else:
            break

    if streak >= 6:
        return [BearishEvent(
            ticker=ticker,
            streak=streak,
            latest_close=round(float(candles["Close"].iloc[-1]), 2),
            timestamp=datetime.now(),
        )]

    return []
