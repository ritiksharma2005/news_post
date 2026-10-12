# News AI Pipeline

## Setup (do this once)

1. **Install Python dependencies:**
   ```
   pip install -r requirements.txt
   ```

2. **Get your API keys:**
   - fetch news from top hindi and Eng News web , ilke Aaj tak and NDTV and Hindu
   - Gemini (free): sign up at https://aistudio.google.com → "Get API key" → create key
   - Telegram bot: message @BotFather on Telegram → `/newbot` → copy the token

3. **Create your `.env` file:**
   ```
   cp .env.example .env
   ```
   Then open `.env` and paste in your real keys.

4. **Test the fetch step:**
   ```
   python fetch_news.py
   ```
   If your keys are correct, this prints how many articles it found from
   each source and saves them to `output/raw_articles.json`.

## What's built so far

- `config.py` — all settings: your priority search topics, file paths, Gemini model name
- `fetch_news.py` — pulls articles from GNews + Guardian, dedupes near-identical
  stories, saves to `output/raw_articles.json`
- `rank_news.py` — sends fetched articles to Gemini (free tier) for scoring against
  your priority tiers (India news > India-relevant international > education
  > social/policy > sports > politics, with an "Indian pride" bonus), merges
  duplicate stories, and saves the top 5 to `output/ranked_articles.json`

## Testing rank_news.py

Run `python fetch_news.py` first (needs real articles to rank), then:
```
python rank_news.py
```
This prints the top 5 stories with their scores and reasons, so you can see
exactly why each one was picked.

## Daily Instagram Broadcast Channel News Digest (@news.nit_iit)

An automated daily workflow that collects all news posts published by `@news.nit_iit` throughout the day, prepares an organized daily roundup with direct Instagram permalinks, and sends a ready-to-copy summary to Telegram for sharing in the [News NIT IIT Instagram Broadcast Channel](https://www.instagram.com/channel/AbYg9NWAeNaKS8gf/).

### How It Works
1. Runs twice daily at **11:00 AM IST** (05:30 UTC — Morning Update) and **9:00 PM IST** (15:30 UTC — Evening Daily Roundup) via GitHub Actions (`.github/workflows/daily_channel_digest.yml`).
2. Fetches all posts published by `@news.nit_iit` during the calendar day in `Asia/Kolkata` (IST) timezone using the official Meta Graph API (with automatic fallback to scrapers).
3. Excludes previous days, duplicate links, and already included posts.
4. Prepares a formatted, numbered roundup:
   ```text
   NEWS NIT IIT — DAILY NEWS ROUNDUP

   Here are today's latest updates from @news.nit_iit. Tap the links to read the complete posts.

   1. [News headline]
      Read here: [Instagram post URL]

   2. [News headline]
      Read here: [Instagram post URL]

   Follow @news.nit_iit for more updates!
   ```
5. Delivers the ready-to-copy text to the configured Telegram bot so the channel admin can copy and paste it into the Instagram Broadcast Channel with one tap.
6. Persists post IDs and roundup state in SQLite (`data/channel_digest.db`) and `data/published_history.json`.

### CLI Usage & Testing
```bash
# Preview today's roundup without sending or updating database
python daily_channel_digest.py --dry-run

# Preview a specific date
python daily_channel_digest.py --date=2026-10-13 --dry-run

# Force regeneration if already completed
python daily_channel_digest.py --force
```

### Instagram Broadcast Channel API Status
Meta Graph API (up to v20.0) does not provide a public REST API endpoint for publishing directly into Instagram Broadcast Channels. To remain fully compliant with Meta policies and protect account health, direct posting uses Telegram as a 1-tap staging bridge instead of unauthorized private APIs or browser automation. An extensible publisher module (`channel_digest/channel_publisher.py`) is prepared for when Meta officially releases public API support.
