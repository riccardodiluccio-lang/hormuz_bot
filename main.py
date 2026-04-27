import os
import asyncio
import feedparser
from datetime import datetime
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ================= CONFIG =================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("Missing TELEGRAM_TOKEN or CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# ================= STATE =================
alert_mode = False
alert_counter = 0

# ================= RSS SOURCES =================
RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://news.google.com/rss/search?q=Strait+of+Hormuz",
    "https://news.google.com/rss/search?q=Iran+oil+shipping"
]

KEYWORDS = [
    "hormuz", "strait", "iran", "oil",
    "shipping", "tankers", "middle east", "usa"
]

# ================= FETCH NEWS =================
def fetch_news():
    news = []

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)

        for entry in feed.entries[:10]:
            title = entry.title
            link = getattr(entry, "link", "no source")

            text = title.lower()

            if any(k in text for k in KEYWORDS):
                news.append({"title": title, "link": link})

    return news[:15]

# ================= DETECT REOPENING =================
def detect_reopening(news):
    triggers = ["reopened", "reopen", "resumed", "traffic restored", "blockade lifted"]

    for n in news:
        t = n["title"].lower()
        if any(x in t for x in triggers):
            return True
    return False

# ================= AI SUMMARY =================
def summarize(news):
    if not news:
        return "No relevant activity detected."

    if len(news) < 3:
        tone = "🟢 LOW ACTIVITY"
    elif len(news) < 7:
        tone = "🟡 MODERATE ACTIVITY"
    else:
        tone = "🔴 HIGH ACTIVITY"

    keywords = {}
    for n in news:
        for k in ["iran", "oil", "shipping", "usa", "strait"]:
            if k in n["title"].lower():
                keywords[k] = keywords.get(k, 0) + 1

    signal = ", ".join([f"{k}:{v}" for k, v in keywords.items()]) if keywords else "no signals"

    return f"""
{tone}

SIGNAL ANALYSIS:
{signal}

INTERPRETATION:
Automated OSINT scan indicates current information flow based on global news sources.
"""

# ================= FORMAT MESSAGE =================
def format_message(news):
    now = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")

    summary = summarize(news)

    news_block = ""
    for n in news[:10]:
        news_block += f"📰 {n['title']}\n🔗 {n['link']}\n\n"

    return f"""
🌊 STRAIT OF HORMUZ — OSINT INTELLIGENCE

📅 {now}

====================
AI SUMMARY
====================
{summary}

====================
NEWS FEED
====================
{news_block if news_block else "No news available"}

====================
SYSTEM STATUS
====================
Monitoring active via RSS sources
"""

# ================= SEND LOGIC =================
async def send_update():
    global alert_mode, alert_counter

    news = fetch_news()

    # trigger alert mode
    if detect_reopening(news):
        alert_mode = True
        alert_counter = 15

    # ALERT MODE
    if alert_mode:
        msg = f"""
🚨 STRAIT OF HORMUZ STATUS CHANGE DETECTED 🚨

POSSIBLE MAJOR CHANGE IN MARITIME CONDITIONS

ALERT ACTIVE

REMAINING MINUTES: {alert_counter}
"""
        alert_counter -= 1

        if alert_counter <= 0:
            alert_mode = False

        await bot.send_message(chat_id=CHAT_ID, text=msg.upper())

    else:
        msg = format_message(news)

        await bot.send_message(chat_id=CHAT_ID, text=msg)

# ================= MAIN LOOP =================
async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_update, "interval", minutes=1)
    scheduler.start()

    await send_update()

    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
