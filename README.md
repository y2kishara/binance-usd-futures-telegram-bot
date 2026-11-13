# Binance USD Futures Telegram Bot

Reads the visible **USD Futures** ranking section from the Binance website and sends the 10 displayed rows to Telegram every 10 minutes.

- Source: https://www.binance.com/en/markets/trading_data/rankings
- Data collected from the rendered website using Playwright (no Binance API or database).
- Fields: rank, symbol, contract type, price, and percentage change.
- Scheduled with GitHub Actions.
- Timestamps use Sri Lanka time (Asia/Colombo).

## Required GitHub Actions secrets

Open **Settings → Secrets and variables → Actions → New repository secret** and add:

1. `TELEGRAM_BOT_TOKEN` — token from BotFather.
2. `TELEGRAM_CHAT_ID` — your Telegram chat or group ID.

Never put either value directly in source code or commit them to this repository.

## Run manually

Open **Actions → Binance USD Futures Telegram Scanner → Run workflow**.

The workflow also runs automatically every 10 minutes. GitHub Actions cron uses UTC; `*/10 * * * *` means every 10 minutes. GitHub-hosted scheduled runs may start a little later than the exact minute.

## Notes

This project reads the public website's visible content. Binance may change its page layout or restrict automated browser traffic; if that happens, the workflow log will show an extraction error and the parser may need updating.
