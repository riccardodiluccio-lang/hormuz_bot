import os
import asyncio
import feedparser
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

# === CONFIG ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("Missing TELEGRAM_TOKEN or CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# === FONTI NEWS ===
RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://news.google.com/rss/search?q=Strait+of+Hormuz&hl=en-US&gl=US&ceid=US:en"
]

KEYWORDS = [
    "hormuz",
    "strait of hormuz",
    "iran",
    "oil",
    "shipping",
    "tankers",
    "middle east"
]

# === FETCH NEWS ===
def fetch_news():
    articles = []

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)

        for entry in feed.entries[:5]:
            title = entry.title
            summary = getattr(entry, "summary", "")

            text = f"{title} {summary}".lower()

            if any(k in text for k in KEYWORDS):
                articles.append(f"📰 {title}")

    return articles[:10]

# === FORMAT ===
def format_report(articles):
    now = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")

    if not articles:
        news_text = "⚠️ Nessuna news rilevante trovata al momento"
    else:
        news_text = "\n".join(articles)

    return f"""
🌊 STRAIT OF HORMUZ — OSINT MONITOR

📅 {now}

📰 NEWS GLOBALI RILEVANTI:
{news_text}

📡 Fonti: BBC / Al Jazeera / NYT / Google News
🤖 Auto-monitoraggio attivo (Railway)
"""

# === SEND ===
async def send_update():
    articles = fetch_news()
    message = format_report(articles)

    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message
        )
        print("Update sent")
    except Exception as e:
        print("Error:", e)

# === LOOP ===
async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_update, "interval", minutes=15)
    scheduler.start()

    await send_update()

    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
