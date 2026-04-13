import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

from scanner import Event
from atr_scanner import ATREvent

load_dotenv()

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

_SMA_EVENT_COLORS = {
    "CROSS_ABOVE":        "#1a7f37",
    "CROSS_BELOW":        "#d1242f",
    "TOUCH_FROM_ABOVE":   "#555555",
    "TOUCH_FROM_BELOW":   "#555555",
}

_ATR_ACTION_COLORS = {
    "ENTERED": "#d1242f",
    "EXITED":  "#1a7f37",
}


def _ts() -> str:
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")


def _row(cells: list[str], bg: str) -> str:
    tds = "".join(
        f'<td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;">{c}</td>'
        for c in cells
    )
    return f'<tr style="background:{bg};">{tds}</tr>'


def _section_header(title: str, color: str, colspan: int) -> str:
    return (
        f'<tr><td colspan="{colspan}" style="'
        f"background:{color};color:#ffffff;font-weight:bold;"
        f'padding:10px 12px;font-size:14px;">{title}</td></tr>'
    )


def _col_header(labels: list[str]) -> str:
    ths = "".join(
        f'<th style="padding:8px 12px;text-align:left;'
        f'background:#f0f0f0;border-bottom:2px solid #cccccc;'
        f'font-size:12px;color:#444;">{l}</th>'
        for l in labels
    )
    return f"<tr>{ths}</tr>"


def _build_html(
    sma_alerts: list[Event],
    atr_alerts: list[ATREvent],
    tickers_scanned: int,
) -> str:
    date_str = datetime.now().strftime("%B %d, %Y")
    total    = len(sma_alerts) + len(atr_alerts)

    table_style = (
        'style="border-collapse:collapse;width:100%;'
        'font-family:Arial,sans-serif;font-size:13px;"'
    )

    sections: list[str] = []

    # ── SMA 150 section ──────────────────────────────────────────────────────
    if sma_alerts:
        rows = [
            _section_header(f"SMA 150 ALERTS ({len(sma_alerts)})", "#1a56a0", 3),
            _col_header(["Ticker", "Signal", "Details"]),
        ]
        for i, e in enumerate(sma_alerts):
            sign  = "+" if e.distance_pct >= 0 else ""
            color = _SMA_EVENT_COLORS.get(e.event_type, "#555555")
            bg    = "#ffffff" if i % 2 == 0 else "#f7f7f7"
            rows.append(_row([
                f'<strong>{e.ticker}</strong>',
                f'<span style="color:{color};font-weight:bold;">{e.event_type}</span>',
                f'SMA {e.ma_period} &nbsp;|&nbsp; '
                f'Close: <strong>{e.latest_close:.2f}</strong> &nbsp;|&nbsp; '
                f'MA: {e.ma_value:.2f} &nbsp;|&nbsp; '
                f'Dist: <strong>{sign}{e.distance_pct:.2f}%</strong>',
            ], bg))
        sections.append(f'<table {table_style}>{"".join(rows)}</table>')

    # ── ATR Pullback section ─────────────────────────────────────────────────
    if atr_alerts:
        rows = [
            _section_header(f"ATR PULLBACK ALERTS ({len(atr_alerts)})", "#b85c00", 3),
            _col_header(["Ticker", "Signal", "Details"]),
        ]
        for i, e in enumerate(atr_alerts):
            action_color = _ATR_ACTION_COLORS.get(e.action, "#555555")
            bg = "#ffffff" if i % 2 == 0 else "#f7f7f7"
            rows.append(_row([
                f'<strong>{e.ticker}</strong>',
                f'<span style="color:{action_color};font-weight:bold;">'
                f'{e.action} {e.volatility_tier}</span>',
                f'ATR: <strong>{e.atr_pct:.2f}%</strong> &nbsp;|&nbsp; '
                f'Pullback: <strong>{e.current_pullback:.1f}%</strong> &nbsp;|&nbsp; '
                f'52W High: {e.week52_high:.2f} &nbsp;|&nbsp; '
                f'Close: <strong>{e.latest_close:.2f}</strong>',
            ], bg))
        sections.append(f'<table {table_style}>{"".join(rows)}</table>')

    body_sections = '<div style="height:16px;"></div>'.join(sections)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
  <div style="max-width:680px;margin:24px auto;background:#ffffff;
              border-radius:6px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.12);">

    <!-- Header -->
    <div style="background:#0d1117;padding:18px 24px;">
      <div style="color:#ffffff;font-size:18px;font-weight:bold;">MA Monitor</div>
      <div style="color:#8b949e;font-size:13px;margin-top:4px;">{date_str}</div>
    </div>

    <!-- Alert tables -->
    <div style="padding:20px 24px;">
      {body_sections}
    </div>

    <!-- Footer -->
    <div style="background:#f6f8fa;padding:12px 24px;
                border-top:1px solid #e0e0e0;color:#666;font-size:12px;">
      {total} alert(s) &nbsp;&middot;&nbsp; {tickers_scanned} tickers scanned
    </div>

  </div>
</body>
</html>"""


def send_alert(
    sma_alerts: list[Event],
    atr_alerts: list[ATREvent],
    tickers_scanned: int,
) -> None:
    """Send a single HTML summary email covering SMA and ATR alerts.

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
    html     = _build_html(sma_alerts, atr_alerts, tickers_scanned)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = recipient
    msg.attach(MIMEText(html, "html"))

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
