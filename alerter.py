import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

from scanner import Event
from atr_scanner import ATREvent
from bearish_scanner import BearishEvent

load_dotenv()

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

_SMA_EMOJI = {
    "CROSS_ABOVE":      "📈",
    "TOUCH_FROM_ABOVE": "📈",
    "CROSS_BELOW":      "📉",
    "TOUCH_FROM_BELOW": "📉",
}

_SMA_COLOR = {
    "CROSS_ABOVE":      "#3fb950",
    "TOUCH_FROM_ABOVE": "#3fb950",
    "CROSS_BELOW":      "#f85149",
    "TOUCH_FROM_BELOW": "#f85149",
}

_TIER_EMOJI = {
    "LOW":    "🟢",
    "MEDIUM": "🟡",
    "HIGH":   "🔴",
}


def _ts() -> str:
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")


def _row(cells_html: list[str]) -> str:
    tds = "".join(f'<td style="padding:7px 10px;border-bottom:1px solid #21262d;">{c}</td>' for c in cells_html)
    return f"<tr>{tds}</tr>"


def _build_html(
    sma_alerts: list[Event],
    atr_alerts: list[ATREvent],
    bearish_alerts: list[BearishEvent],
    tickers_scanned: int,
) -> str:
    date_str = datetime.now().strftime("%B %d, %Y")
    total    = len(sma_alerts) + len(atr_alerts) + len(bearish_alerts)

    # ── SMA section ──────────────────────────────────────────────────────────
    sma_html = ""
    if sma_alerts:
        rows = ""
        for e in sma_alerts:
            emoji = _SMA_EMOJI.get(e.event_type, "📊")
            color = _SMA_COLOR.get(e.event_type, "#c9d1d9")
            sign  = "+" if e.distance_pct >= 0 else ""
            rows += _row([
                f'<span style="font-weight:bold;color:#e6edf3;">{e.ticker}</span>',
                f'<span style="color:{color};">{emoji} {e.event_type}</span>',
                f'<span style="color:#8b949e;">SMA {e.ma_period} &nbsp;|&nbsp; '
                f'Close: <span style="color:#e6edf3;">${e.latest_close:.2f}</span> &nbsp;|&nbsp; '
                f'MA: ${e.ma_value:.2f} &nbsp;|&nbsp; '
                f'Dist: <span style="color:{color};">{sign}{e.distance_pct:.2f}%</span></span>',
            ])

        sma_html = f"""
        <div style="margin-bottom:24px;border-left:3px solid #388bfd;padding-left:12px;">
          <div style="color:#388bfd;font-weight:bold;font-size:14px;margin-bottom:8px;">
            &#128202; SMA 150 ALERTS ({len(sma_alerts)})
          </div>
          <table style="width:100%;border-collapse:collapse;font-family:monospace;font-size:13px;">
            {rows}
          </table>
        </div>"""

    # ── ATR section ──────────────────────────────────────────────────────────
    atr_html = ""
    if atr_alerts:
        rows = ""
        for e in atr_alerts:
            tier_emoji = _TIER_EMOJI.get(e.volatility_tier, "⚪")
            rows += _row([
                f'<span style="font-weight:bold;color:#e6edf3;">{e.ticker}</span>',
                f'<span style="color:#f85149;font-weight:bold;">{e.current_pullback:.1f}%</span>'
                f'<span style="color:#8b949e;"> from 52W High &nbsp;(ATR: {e.atr_pct:.2f}% {tier_emoji})</span>',
            ])

        atr_html = f"""
        <div style="margin-bottom:24px;border-left:3px solid #d29922;padding-left:12px;">
          <div style="color:#d29922;font-weight:bold;font-size:14px;margin-bottom:8px;">
            &#128201; ATR PULLBACK ALERTS ({len(atr_alerts)})
          </div>
          <table style="width:100%;border-collapse:collapse;font-family:monospace;font-size:13px;">
            {rows}
          </table>
        </div>"""

    # ── Bearish streak section ────────────────────────────────────────────────
    bearish_html = ""
    if bearish_alerts:
        rows = ""
        for e in bearish_alerts:
            rows += _row([
                f'<span style="font-weight:bold;color:#e6edf3;">{e.ticker}</span>',
                f'<span style="color:#da3633;font-weight:bold;">{e.red_count}/7 red candles</span>'
                f'<span style="color:#8b949e;"> &nbsp;|&nbsp; Close: '
                f'<span style="color:#e6edf3;">${e.latest_close:.2f}</span></span>',
            ])

        bearish_html = f"""
        <div style="margin-bottom:24px;border-left:3px solid #da3633;padding-left:12px;">
          <div style="color:#da3633;font-weight:bold;font-size:14px;margin-bottom:8px;">
            &#128308; BEARISH STREAK ALERTS ({len(bearish_alerts)})
          </div>
          <table style="width:100%;border-collapse:collapse;font-family:monospace;font-size:13px;">
            {rows}
          </table>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="margin:0;padding:0;background:#0d1117;font-family:monospace;">
  <div style="max-width:700px;margin:0 auto;background:#0d1117;color:#c9d1d9;">

    <!-- Header -->
    <div style="padding:24px 24px 16px 24px;border-bottom:1px solid #21262d;">
      <div style="font-size:22px;font-weight:bold;color:#e6edf3;letter-spacing:0.5px;">
        MA Monitor
      </div>
      <div style="font-size:13px;color:#8b949e;margin-top:4px;">{date_str}</div>
    </div>

    <!-- Alerts -->
    <div style="padding:20px 24px;">
      {sma_html}
      {atr_html}
      {bearish_html}
    </div>

    <!-- Footer -->
    <div style="padding:12px 24px;border-top:1px solid #21262d;
                font-size:12px;color:#8b949e;font-family:monospace;">
      {total} alert(s) &nbsp;&#183;&nbsp; {tickers_scanned} tickers scanned
    </div>

  </div>
</body>
</html>"""


def send_alert(
    sma_alerts: list[Event],
    atr_alerts: list[ATREvent],
    bearish_alerts: list[BearishEvent],
    tickers_scanned: int,
) -> None:
    """Send a single HTML summary email covering SMA, ATR, and bearish alerts.

    Silent if all lists are empty. Logs and returns on any error — never raises.
    """
    if not sma_alerts and not atr_alerts and not bearish_alerts:
        return

    sender    = os.getenv("EMAIL_SENDER", "")
    password  = os.getenv("EMAIL_PASSWORD", "")
    recipient = os.getenv("EMAIL_RECIPIENT", "")

    if not sender or not password or not recipient:
        print(f"{_ts()} ERROR: Email credentials missing — check your .env file")
        return

    total    = len(sma_alerts) + len(atr_alerts) + len(bearish_alerts)
    date_str = datetime.now().strftime("%B %d, %Y")
    subject  = f"MA Monitor — {total} Alert(s) — {date_str}"
    html     = _build_html(sma_alerts, atr_alerts, bearish_alerts, tickers_scanned)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = recipient
    msg.attach(MIMEText(html, "html", "utf-8"))

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
