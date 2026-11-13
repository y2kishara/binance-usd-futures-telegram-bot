import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from playwright.sync_api import sync_playwright

BINANCE_URL = "https://www.binance.com/en/markets/trading_data/rankings"
LOCAL_TZ = ZoneInfo("Asia/Colombo")


def extract_usd_futures():
    """Read the visible USD Futures ranking section from Binance's web page."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(
            viewport={"width": 1440, "height": 1100},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
            ),
        )
        page.goto(BINANCE_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(9000)
        body_text = page.locator("body").inner_text(timeout=30000)
        browser.close()

    # Binance may label this section "USD Futures" or "USDⓈ-M Futures".
    heading_match = re.search(r"USD(?:Ⓢ-M)? Futures", body_text, flags=re.IGNORECASE)
    if not heading_match:
        raise RuntimeError("Could not find the USD Futures section on the Binance page.")

    section_text = body_text[heading_match.end():]
    next_section = re.search(r"\n\s*(?:Coin Futures|COIN-M Futures|Options)\s*\n", section_text, re.I)
    if next_section:
        section_text = section_text[:next_section.start()]

    lines = [line.strip() for line in section_text.splitlines() if line.strip()]

    # Remove the column headings if they are present.
    while lines and lines[0].lower() in {"name", "price", "change", "24h change"}:
        lines.pop(0)

    rows = []
    i = 0
    while i < len(lines):
        if not re.fullmatch(r"\d+", lines[i]):
            i += 1
            continue

        # Expected visible row: rank, symbol, contract, price, percentage change.
        if i + 4 >= len(lines):
            break

        rank, symbol, contract, price, change = lines[i:i + 5]
        if (
            re.fullmatch(r"\d+", rank)
            and re.fullmatch(r"[A-Z0-9._-]+", symbol, re.I)
            and re.search(r"USDT|USD", symbol, re.I)
            and re.search(r"Perpetual|Quarterly|Monthly|Delivery", contract, re.I)
            and re.search(r"\d", price)
            and re.fullmatch(r"[+-]?\d+(?:\.\d+)?%", change)
        ):
            rows.append({
                "rank": rank,
                "symbol": symbol,
                "contract": contract,
                "price": price,
                "change": change,
            })
            i += 5
        else:
            i += 1

    if len(rows) < 10:
        preview = "\n".join(lines[:80])
        raise RuntimeError(
            f"Expected 10 USD Futures rows but extracted {len(rows)}. "
            f"Binance page layout may have changed. Section preview:\n{preview}"
        )

    return rows[:10]


def format_message(rows):
    now = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %I:%M:%S %p")
    parts = [
        "📊 BINANCE USD FUTURES RANKINGS",
        f"🕒 Updated: {now} (Sri Lanka time)",
        "━━━━━━━━━━━━━━━━━━",
    ]

    for item in rows:
        change = item["change"]
        emoji = "🟢" if change.startswith("+") else "🔴" if change.startswith("-") else "⚪"
        parts.extend([
            f'{item["rank"]}. {item["symbol"]}',
            f'   Contract: {item["contract"]}',
            f'   Price: {item["price"]}',
            f'   Change: {emoji} {change}',
            "",
        ])

    parts.extend([
        "━━━━━━━━━━━━━━━━━━",
        "Source: Binance website",
    ])
    return "\n".join(parts).strip()


def send_telegram_message(message):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    response = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": True,
        },
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(f"Telegram returned an error: {result}")


def main():
    rows = extract_usd_futures()
    message = format_message(rows)
    send_telegram_message(message)
    print(f"Successfully sent {len(rows)} USD Futures rows to Telegram.")


if __name__ == "__main__":
    main()
