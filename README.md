# MA Monitor

Scans a watchlist of ~145 stocks once daily after US market close and sends a
single email summary whenever a closing price crosses or touches the 150-day SMA.

---

## Setup

```bash
pip install -r requirements.txt
```

---

## Configure email credentials

1. Copy the example env file:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` and fill in your Gmail details:

   ```
   EMAIL_SENDER=you@gmail.com
   EMAIL_PASSWORD=your_app_password
   EMAIL_RECIPIENT=recipient@gmail.com
   ```

   > **Gmail app password**: Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords),
   > create a new app password for "Mail", and paste the 16-character code as
   > `EMAIL_PASSWORD`. This is separate from your main Gmail password and works
   > even with 2FA enabled.

---

## Run on schedule

```bash
python main.py
```

Starts the scheduler. Scans daily at **23:05 Asia/Jerusalem** (after US market
close). Prints the next scheduled run time on startup.

---

## Test scan immediately

```bash
python main.py --now
```

Runs a full scan right now — useful for verifying setup, testing email delivery,
and checking the watchlist without waiting for the scheduled time.

---

## How it works

1. **Fetch** — downloads ~1 year of daily OHLCV data per ticker via yfinance
2. **Scan** — computes SMA 150 on the Close column; detects four event types:
   - `CROSS_ABOVE` — price closed below SMA yesterday, above today
   - `CROSS_BELOW` — price closed above SMA yesterday, below today
   - `TOUCH_FROM_ABOVE` — price is within 0.5% above the SMA (no cross)
   - `TOUCH_FROM_BELOW` — price is within 0.5% below the SMA (no cross)
3. **Debounce** — each ticker is silenced for 3 days after an alert fires
   (stored in `state.json`)
4. **Email** — if any events were detected, one summary email is sent with
   all alerts; silent scan if nothing triggered

---

## Project structure

```
ma_monitor/
├── main.py          — entry point, starts scheduler
├── config.py        — watchlist, MA settings, email config
├── fetcher.py       — yfinance data fetching
├── scanner.py       — SMA calculation + event detection
├── alerter.py       — Gmail email sending
├── state_manager.py — debounce state via state.json
├── state.json       — auto-created on first alert
├── requirements.txt
└── .env             — email credentials (never commit this)
```

---

## Sample email

```
--------------------------------------------
MA Monitor Daily Scan — April 13, 2025
--------------------------------------------
NVDA   CROSS_ABOVE          SMA 150  Close: 875.30  MA: 871.10  Dist: +0.48%
TSLA   TOUCH_FROM_BELOW     SMA 150  Close: 172.45  MA: 173.20  Dist: -0.43%
MOD    CROSS_BELOW          SMA 150  Close: 44.10   MA: 44.85   Dist: -1.67%
--------------------------------------------
3 event(s) detected across 145 tickers scanned.
```
