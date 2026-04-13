import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

from dotenv import load_dotenv

from scanner import Event
from atr_scanner import ATREvent

load_dotenv()

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

_SMA_EMOJI = {
    "CROSS_ABOVE":       "📈",
    "TOUCH_FROM_ABOVE":  "📈",
    "CROSS_BELOW":       "📉",
    "TOUCH_FROM_BELOW":  "📉",
}

_TIER_EMOJI = {
    "LOW":    "🟢",
    "MEDIUM": "🟡",
    "HIGH":   "🔴",
}


def _ts() -> str:
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")


def _build_body(
    sma_alerts: list[Event],
    atr_alerts: list[ATREvent],
    tickers_scanned: int,
) -> str:
    date_str = datetime.now().strftime("%B %d, %Y")
    total    = len(sma_alerts) + len(atr_alerts)
    sep      = "-" * 36

    lines = [
        sep,
        f"MA Monitor — {date_str}",
        sep,
    ]

    if sma_alerts:
        lines.append("")
        lines.append(f"📊 SMA 150 ALERTS ({len(sma_alerts)})")
        for e in sma_alerts:
            emoji = _SMA_EMOJI.get(e.event_type, "📊")
            sign  = "+" if e.distance_pct >= 0 else ""
            lines.append(
                f"{e.ticker} {emoji} SMA {e.ma_period} — "
                f"Close: ${e.latest_close:.2f} | "
                f"MA: ${e.ma_value:.2f} | "
                f"Dist: {sign}{e.distance_pct:.2f}%"
            )

    if atr_alerts:
        lines.append("")
        lines.append(f"📉 ATR PULLBACK ALERTS ({len(atr_alerts)})")
        for e in atr_alerts:
            circle = _TIER_EMOJI.get(e.volatility_tier, "⚪")
            lines.append(
                f"{e.ticker} ({e.atr_pct:.2f}%) {circle} — "
                f"Pullback: {e.current_pullback:.1f}% | "
                f"52W High: ${e.week52_high:.2f} | "
                f"Close: ${e.latest_close:.2f}"
            )

    lines.append("")
    lines.append(sep)
    lines.append(f"{total} alert(s) | {tickers_scanned} tickers scanned")
    return "\n".join(lines)


def send_alert(
    sma_alerts: list[Event],
    atr_alerts: list[ATREvent],
    tickers_scanned: int,
) -> None:
    """Send a single plain-text summary email covering SMA and ATR alerts.

    Silent if both lists are empty. Logs and returns on any error — never raises.
    """
    if not sma_alerts and not atr_alerts:
        return

    sender    = os.getenv("EMAIL_SENDER", "")
    password  = os.getenv("EMAIL_PASSWORD", "")
    recipient = os.getenv("EMAIL_RECIPIENT", "")

    if not sender or not password or not recipient:
        print(f"{_ts()} ERROR: Email credentials missing — check your .env file")
        return

    total    = len(sma_alerts) + len(atr_alerts)
    date_str = datetime.now().strftime("%B %d, %Y")
    subject  = f"MA Monitor — {total} Alert(s) — {date_str}"
    body     = _build_body(sma_alerts, atr_alerts, tickers_scanned)

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = recipient

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(sender, password)
            smtp.sendmail(sender, recipient, msg.as_string())
        print(f"{_ts()} Email sent: {subject}")
    except smtplib.SMTPException as exc:
        print(f"{_ts()} ERROR: Failed to send email — {exc}")
    except Exception as exc:
        print(f"{_ts()} ERROR: Unexpected error sending email — {exc}")
