import argparse
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from config import WATCHLIST, MA_PERIOD, SCAN_TIME, TIMEZONE
from fetcher import fetch_ticker
from scanner import scan_ticker
from atr_scanner import scan_atr
from bearish_scanner import scan_bearish
from alerter import send_alert


def _ts() -> str:
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")


def run_scan() -> None:
    print(f"{_ts()} Scan started — {len(WATCHLIST)} tickers")

    sma_alerts     = []
    atr_alerts     = []
    bearish_alerts = []
    scanned        = 0

    for ticker in WATCHLIST:
        df = fetch_ticker(ticker)
        if df is None:
            continue
        scanned += 1

        sma_alerts.extend(scan_ticker(ticker, df))
        atr_alerts.extend(scan_atr(ticker, df))
        bearish_alerts.extend(scan_bearish(ticker, df))

    total = len(sma_alerts) + len(atr_alerts) + len(bearish_alerts)
    if sma_alerts or atr_alerts or bearish_alerts:
        send_alert(sma_alerts, atr_alerts, bearish_alerts, scanned)
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
