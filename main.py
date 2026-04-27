import os
import asyncio
import feedparser
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from openai import OpenAI

# ================= CONFIG =================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("Missing TELEGRAM_TOKEN")

bot_app = None
client = OpenAI(api_key=OPENAI_API_KEY)

# ================= STATE =================
last_report = ""
last_event_state = False

# ================= RSS =================
RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://news.google.com/rss/search?q=Strait+of+Hormuz",
    "https://news.google.com/rss/search?q=Iran+oil+shipping"
]

KEYWORDS = ["hormuz", "iran", "oil", "shipping", "strait", "usa", "middle east"]

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
def ai_summary(news_text):
    if not news_text:
        return "Nessun aggiornamento rilevante."

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Sei un analista OSINT. Riassumi in italiano in modo chiaro e breve."},
            {"role": "user", "content": "\n".join(news_text)}
        ]
    )

    return res.choices[0].message.content

# ================= FORMAT =================
def build_report(news):
    now = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")

    summary = ai_summary(news)

    block = "\n".join(news)

    return f"""
🌊 STRETTO DI HORMUZ — INTELLIGENCE REPORT

📅 {now}

🧠 RIASSUNTO AI:
{summary}

📰 FONTI:
{block}
"""

# ================= DETECT EVENT =================
def detect_event(news):
    triggers = ["reopened", "reopen", "resumed", "traffic restored", "blockade lifted"]

    return any(any(t in n.lower() for t in triggers) for n in news)

# ================= AUTO REPORT =================
async def send_update():
    global last_report, last_event_state

    news = fetch_news()
    report = build_report(news)

    event = detect_event(news)

    # 🚨 ALERT SOLO SE CAMBIA STATO
    if event and not last_event_state:
        alert = "🚨 CAMBIO CONDIZIONI NELLO STRETTO DI HORMUZ"
        await bot_app.bot.send_message(chat_id=CHAT_ID, text=alert)

    last_event_state = event

    # ❌ BLOCCO DUPLICATI
    if report == last_report:
        return

    last_report = report

    await bot_app.bot.send_message(chat_id=CHAT_ID, text=report)

# ================= CHAT =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Sei un analista OSINT sullo Stretto di Hormuz."},
            {"role": "user", "content": user_text}
        ]
    )

    await update.message.reply_text(res.choices[0].message.content)

# ================= MAIN =================
async def main():
    global bot_app

    bot_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_update, "interval", minutes=5)
    scheduler.start()

    await send_update()

    print("Bot attivo")

    await bot_app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
