from dataclasses import dataclass
from datetime import datetime

import pandas as pd


@dataclass
class ATREvent:
    ticker: str
    action: str             # "ENTERED" | "EXITED"
    atr_value: float        # raw ATR in dollars
    atr_pct: float          # ATR as % of price
    volatility_tier: str    # "HIGH" | "MEDIUM" | "LOW"
    pullback_threshold: float
    current_pullback: float  # negative: e.g. -38.2 means 38.2% below 52W high
    week52_high: float
    latest_close: float
    timestamp: datetime


def _tier_and_threshold(atr_pct: float) -> tuple[str, float]:
    if atr_pct >= 6.0:
        return "HIGH", 35.0
    if atr_pct >= 3.0:
        return "MEDIUM", 22.0
    return "LOW", 10.0


def _compute(ticker: str, df: pd.DataFrame) -> ATREvent | None:
    """Compute ATR, volatility tier, and 52-week pullback for *ticker*.

    Returns an ATREvent with action="" — the caller sets the action field.
    Returns None if there is insufficient data.
    """
    if df is None or df.empty:
        return None

    df = df.copy().reset_index(drop=True)
    required_cols = {"High", "Low", "Close"}
    if not required_cols.issubset(df.columns):
        return None

    if len(df) < 15:
        return None

    # --- True Range ---
    prev_close = df["Close"].shift(1)
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - prev_close).abs(),
        (df["Low"]  - prev_close).abs(),
    ], axis=1).max(axis=1)

    tr = tr.dropna()
    if len(tr) < 14:
        return None

    # --- Wilder ATR (14-period) ---
    atr = float(tr.iloc[:14].mean())
    for val in tr.iloc[14:]:
        atr = (atr * 13 + val) / 14

    latest_close = float(df["Close"].iloc[-1])
    if latest_close <= 0:
        return None

    atr_pct = (atr / latest_close) * 100
    tier, threshold = _tier_and_threshold(atr_pct)

    # --- 52-week high (last 252 trading days) ---
    week52_high = float(df["Close"].tail(252).max())
    current_pullback = (latest_close - week52_high) / week52_high * 100

    return ATREvent(
        ticker=ticker,
        action="",
        atr_value=round(atr, 4),
        atr_pct=round(atr_pct, 2),
        volatility_tier=tier,
        pullback_threshold=threshold,
        current_pullback=round(current_pullback, 2),
        week52_high=round(week52_high, 2),
        latest_close=round(latest_close, 2),
        timestamp=datetime.now(),
    )


def scan_atr(ticker: str, df: pd.DataFrame) -> list[ATREvent]:
    """Return [ATREvent] if the stock has pulled back past its tier's threshold.

    Returns an empty list otherwise.
    No imports from alerter.py or main.py — fully self-contained.
    Importable as: from atr_scanner import scan_atr, ATREvent
    """
    event = _compute(ticker, df)
    if event is None:
        return []

    if abs(event.current_pullback) >= event.pullback_threshold:
        event.action = "ENTERED"
        return [event]

    return []


def get_atr_snapshot(ticker: str, df: pd.DataFrame) -> ATREvent | None:
    """Return current ATR data regardless of whether the threshold is breached.

    Used by main.py solely for exit-zone detection — when a ticker was
    previously marked IN but no longer meets its pullback threshold.
    """
    event = _compute(ticker, df)
    if event is None:
        return None
    event.action = "EXITED"
    return event
