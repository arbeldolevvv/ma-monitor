import json
import os
from datetime import date, datetime

from config import DEBOUNCE_DAYS

STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")


def _ts() -> str:
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")


def load_state() -> dict:
    """Read state.json and return its contents as a dict.

    Returns an empty dict if the file is missing or corrupted.
    """
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"{_ts()} WARNING: state.json corrupted ({exc}) — resetting to empty state")
        return {}


def save_state(state: dict) -> None:
    """Persist *state* to state.json."""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def _key(ticker: str, ma_period: int) -> str:
    return f"{ticker}_{ma_period}"


def should_alert(state: dict, ticker: str, ma_period: int, today: date) -> bool:
    """Return True if we should send an alert for this ticker/MA combo today.

    Suppressed when an alert was already sent within DEBOUNCE_DAYS days.
    """
    k = _key(ticker, ma_period)
    if k not in state:
        return True
    try:
        last_date = date.fromisoformat(state[k])
        return (today - last_date).days >= DEBOUNCE_DAYS
    except (ValueError, TypeError):
        return True


def mark_alerted(state: dict, ticker: str, ma_period: int, today: date) -> None:
    """Record that an alert was sent for *ticker* today."""
    state[_key(ticker, ma_period)] = today.isoformat()


# ---------------------------------------------------------------------------
# ATR zone state helpers
# ---------------------------------------------------------------------------

def _atr_key(ticker: str, tier: str) -> str:
    return f"ATR_{ticker}_{tier}"


def should_alert_atr(state: dict, ticker: str, tier: str) -> bool:
    """Return True if the ticker/tier has not already been marked IN.

    ATR alerts fire on zone entry only — no date-based debounce.
    """
    k = _atr_key(ticker, tier)
    if k not in state:
        return True
    return state[k].get("status") != "IN"


def mark_alerted_atr(state: dict, ticker: str, tier: str, today: date) -> None:
    """Mark ticker/tier as IN zone (alert was sent for entry)."""
    state[_atr_key(ticker, tier)] = {"status": "IN", "date": today.isoformat()}


def mark_exited_atr(state: dict, ticker: str, tier: str, today: date) -> None:
    """Mark ticker/tier as OUT of zone (exit alert was sent)."""
    state[_atr_key(ticker, tier)] = {"status": "OUT", "date": today.isoformat()}
