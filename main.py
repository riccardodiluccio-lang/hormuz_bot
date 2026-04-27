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

# ================= RSS SOURCES =================
RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://news.google.com/rss/search?q=Strait+of+Hormuz",
    "https://news.google.com/rss/search?q=Iran+oil+shipping",
]

KEYWORDS = [
    "hormuz", "strait", "iran", "usa", "oil",
    "tankers", "shipping", "middle east", "war"
]

# ================= FETCH NEWS =================
def fetch_news():
    news = []

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)

        for entry in feed.entries[:10]:
            title = entry.title
            link = entry.link if hasattr(entry, "link") else "No source"

            text = title.lower()

            if any(k in text for k in KEYWORDS):
                news.append({
                    "title": title,
                    "source": link
                })

    return news[:15]

# ================= AI SUMMARY (SIMULATO MA INTELLIGENTE) =================
def summarize(news):
    if not news:
        return "No significant developments detected in monitored region."

    titles = [n["title"] for n in news]

    if len(news) <= 3:
        tone = "🟢 Low activity detected in the region."
    elif len(news) <= 7:
        tone = "🟡 Moderate activity with geopolitical signals."
    else:
        tone = "🔴 High information flow — possible escalation indicators."

    # mini “AI-style summary”
    keywords_hit = {}
    for n in titles:
        for k in ["iran", "oil", "shipping", "us", "attack", "strait"]:
            if k in n.lower():
                keywords_hit[k] = keywords_hit.get(k, 0) + 1

    keyword_summary = ", ".join(
        [f"{k}({v})" for k, v in keywords_hit.items()]
    ) if keywords_hit else "no dominant signals"

    return f"""
{tone}

📊 Signal analysis:
{keyword_summary}

🧠 Interpretation:
Activity detected across multiple geopolitical/news sources,
but no verified confirmation of escalation at this time.
"""

# ================= FORMAT MESSAGE =================
def format_message(news):
    now = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")

    summary = summarize(news)

    news_block = ""
    for n in news[:10]:
        news_block += f"📰 {n['title']}\n🔗 {n['source']}\n\n"

    return f"""
🌊 STRAIT OF HORMUZ — OSINT INTELLIGENCE REPORT

📅 {now}

=====================
🧠 AI SUMMARY
=====================
{summary}

=====================
📰 LIVE NEWS FEED
=====================
{news_block if news_block else "No relevant news found."}

=====================
🤖 SYSTEM STATUS
=====================
✔ Monitoring active (RSS global feeds)
✔ Filtering geopolitical signals
✔ Running on Railway 24/7
"""

# ================= SEND =================
async def send_update():
    news = fetch_news()
    message = format_message(news)

    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            disable_web_page_preview=True
        )
        print("Update sent")
    except Exception as e:
        print("Error:", e)

# ================= LOOP =================
async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_update, "interval", minutes=15)
    scheduler.start()

    await send_update()

    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
