import argparse
from datetime import datetime, date

from apscheduler.schedulers.blocking import BlockingScheduler

from config import WATCHLIST, MA_PERIOD, SCAN_TIME, TIMEZONE
from fetcher import fetch_ticker
from scanner import scan_ticker
from atr_scanner import scan_atr, get_atr_snapshot
from state_manager import (
    load_state, save_state,
    should_alert, mark_alerted,
    should_alert_atr, mark_alerted_atr, mark_exited_atr,
)
from alerter import send_alert


def _ts() -> str:
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")


def run_scan() -> None:
    print(f"{_ts()} Scan started — {len(WATCHLIST)} tickers")

    state      = load_state()
    today      = date.today()
    sma_alerts = []
    atr_alerts = []
    scanned    = 0

    for ticker in WATCHLIST:
        df = fetch_ticker(ticker)   # fetched ONCE per ticker
        if df is None:
            continue
        scanned += 1

        # --- SMA scan ---
        for event in scan_ticker(ticker, df):
            if should_alert(state, ticker, MA_PERIOD, today):
                sma_alerts.append(event)
                mark_alerted(state, ticker, MA_PERIOD, today)

        # --- ATR scan: ENTERED detection ---
        atr_events = scan_atr(ticker, df)
        if atr_events:
            event = atr_events[0]
            if should_alert_atr(state, ticker, event.volatility_tier):
                atr_alerts.append(event)
                mark_alerted_atr(state, ticker, event.volatility_tier, today)
            # else: already IN → silence
        else:
            # EXIT detection: check all tiers this ticker may have been IN
            for tier in ("HIGH", "MEDIUM", "LOW"):
                k = f"ATR_{ticker}_{tier}"
                if state.get(k, {}).get("status") == "IN":
                    snapshot = get_atr_snapshot(ticker, df)
                    if snapshot:
                        snapshot.action = "EXITED"
                        snapshot.volatility_tier = tier  # preserve the tier it was IN
                        atr_alerts.append(snapshot)
                        mark_exited_atr(state, ticker, tier, today)

    total = len(sma_alerts) + len(atr_alerts)
    if sma_alerts or atr_alerts:
        send_alert(sma_alerts, atr_alerts, scanned)
        save_state(state)
        print(f"{_ts()} Scan complete — {total} alert(s) across {scanned} tickers scanned")
    else:
        print(f"{_ts()} Scan complete — no events detected across {scanned} tickers scanned")


def main() -> None:
    parser = argparse.ArgumentParser(description="MA Monitor — SMA 150 alert tool")
    parser.add_argument(
        "--now",
        action="store_true",
        help="Run scan immediately instead of waiting for the scheduled time",
    )
    args = parser.parse_args()

    if args.now:
        run_scan()
        return

    hour, minute = (int(x) for x in SCAN_TIME.split(":"))
    scheduler = BlockingScheduler(timezone=TIMEZONE)
    scheduler.add_job(run_scan, "cron", hour=hour, minute=minute)

    next_run = scheduler.get_jobs()[0].next_run_time
    print(f"MA Monitor running. Next scan at {next_run}.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("MA Monitor stopped.")


if __name__ == "__main__":
    main()
