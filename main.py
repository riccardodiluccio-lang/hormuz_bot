import os
import asyncio
import feedparser
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from openai import OpenAI

# ================= CONFIG =================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise ValueError("Missing TELEGRAM_TOKEN or OPENAI_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

# ================= RSS =================
RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://news.google.com/rss/search?q=Strait+of+Hormuz",
    "https://news.google.com/rss/search?q=Iran+oil+shipping"
]

KEYWORDS = ["hormuz", "iran", "oil", "shipping", "strait", "usa"]

# ================= FETCH =================
def fetch_news():
    news = []

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)

        for entry in feed.entries[:10]:
            title = entry.title
            link = getattr(entry, "link", "")

            if any(k in title.lower() for k in KEYWORDS):
                news.append(f"{title} | {link}")

    return news[:10]

# ================= AI SUMMARY =================
def ai_summary(news):
    if not news:
        return "Nessun dato rilevante."

    text = "\n".join(news)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Sei un analista OSINT. Riassumi in italiano in modo chiaro e breve."},
            {"role": "user", "content": text}
        ]
    )

    return response.choices[0].message.content

# ================= FORMAT =================
def format_report(news):
    now = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")

    summary = ai_summary(news)

    block = "\n".join(news)

    return f"""
🌊 STRETTO DI HORMUZ — OSINT AI REPORT

📅 {now}

🧠 RIASSUNTO AI:
{summary}

📰 FONTI:
{block}
"""

# ================= NEWS LOOP =================
async def send_update():
    news = fetch_news()
    message = format_report(news)

    await bot.send_message(chat_id=CHAT_ID, text=message)

# ================= CHAT FUNCTION =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Sei un analista OSINT sullo Stretto di Hormuz. Rispondi solo usando contesto geopolitico e news."},
            {"role": "user", "content": user_text}
        ]
    )

    answer = response.choices[0].message.content

    await update.message.reply_text(answer)

# ================= MAIN =================
async def main():
    # Telegram app
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_update, "interval", minutes=5)
    scheduler.start()

    await send_update()

    print("Bot AI attivo")

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
