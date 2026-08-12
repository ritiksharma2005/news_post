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

## What's next

- `rewrite_news.py` — rewrites headline + 2-3 line summary for each top story
- `caption.py` — writes social captions + hashtags
- `generate_image.py` + `design_post.py` — builds the visual card
- `telegram_bot.py` — sends you the finished card + caption to review
