# twitch-extension-private

Private data and tooling for RSL Hero Guide Twitch Extension.

## Contents

| Path | Description |
|------|-------------|
| `data/` | heroes.json, skill-multipliers — scraped game data |
| `i18n/heroes-uk.json` | Ukrainian translations (407 heroes, extracted from game) |
| `tools/` | Extraction scripts, scrapers, data pipeline |
| `cf-feedback-worker/` | Cloudflare Worker (feedback → Discord webhook) |

## Public repo

Source code: https://github.com/YOU/twitch-extension

## Data pipeline

```bash
# Refresh l10n from running game (Admin, game must be open):
python tools/read-static-data.py
python tools/build-heroes-uk.py

# Refresh hero portraits:
# see .claude/commands/find-hero-portraits.md in public repo

# Scrape hero list:
node tools/scrape-ayumilove.mjs
```
