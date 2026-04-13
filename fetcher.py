import time
from datetime import datetime

import pandas as pd
import yfinance as yf


def _ts() -> str:
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")


def fetch_ticker(ticker: str) -> pd.DataFrame | None:
    """Download ~1 year of daily OHLCV data for *ticker*.

    Returns a DataFrame with columns [Date, Open, High, Low, Close, Volume]
    or None if the fetch fails or the data is empty.
    """
    try:
        raw = yf.download(
            ticker,
            period="1y",
            interval="1d",
            auto_adjust=True,
            progress=False,
            multi_level_index=False,
        )

        if raw is None or raw.empty:
            print(f"{_ts()} WARNING: No data returned for {ticker}")
            return None

        df = raw.reset_index()[["Date", "Open", "High", "Low", "Close", "Volume"]]
        df = df.dropna(subset=["Close"])

        if df.empty:
            print(f"{_ts()} WARNING: Empty Close data for {ticker}")
            return None

        return df

    except Exception as exc:
        print(f"{_ts()} WARNING: Failed to fetch {ticker} — {exc}")
        return None

    finally:
        time.sleep(0.5)
