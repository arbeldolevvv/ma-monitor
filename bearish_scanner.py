from dataclasses import dataclass
from datetime import datetime

import pandas as pd


@dataclass
class BearishEvent:
    ticker: str
    red_count: int       # number of red candles out of the last 7
    latest_close: float
    timestamp: datetime


def scan_bearish(ticker: str, df: pd.DataFrame) -> list[BearishEvent]:
    """Return [BearishEvent] if 6 or more of the last 7 candles are red.

    A red candle is defined as Close < Open.

    No imports from alerter.py or main.py — fully self-contained.
    Importable as: from bearish_scanner import scan_bearish, BearishEvent
    """
    if df is None or df.empty:
        return []

    required_cols = {"Open", "Close"}
    if not required_cols.issubset(df.columns):
        return []

    candles = df.tail(7).reset_index(drop=True)
    if len(candles) < 7:
        return []

    red_count = sum(
        1 for i in range(len(candles))
        if float(candles["Close"].iloc[i]) < float(candles["Open"].iloc[i])
    )

    if red_count >= 6:
        return [BearishEvent(
            ticker=ticker,
            red_count=red_count,
            latest_close=round(float(candles["Close"].iloc[-1]), 2),
            timestamp=datetime.now(),
        )]

    return []
