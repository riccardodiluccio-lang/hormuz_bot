import os
import asyncio
import feedparser
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ================= CONFIG =================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN:
    raise ValueError("Missing TELEGRAM_TOKEN")

# ================= STATE =================
last_report = ""

# ================= RSS =================
RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://news.google.com/rss/search?q=Strait+of+Hormuz",
    "https://news.google.com/rss/search?q=Iran+oil"
]

KEYWORDS = ["hormuz", "iran", "oil", "shipping", "strait"]

# ================= FETCH NEWS =================
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

# ================= FREE AI (HUGGING FACE) =================
def ai_summary(text):
    if not text:
        return "Nessuna informazione disponibile."

    API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"

    headers = {}
    hf_key = os.getenv("HF_API_KEY")
    if hf_key:
        headers["Authorization"] = f"Bearer {hf_key}"

    payload = {
        "inputs": f"Riassumi in italiano in modo semplice: {text}"
    }

    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        result = r.json()

        if isinstance(result, list) and "generated_text" in result[0]:
            return result[0]["generated_text"]

        return "Riassunto non disponibile, ma news ricevute correttamente."

    except:
        return "Errore AI, ma news disponibili."

# ================= FORMAT =================
def format_report(news):
    now = datetime.now().strftime("%d/%m/%Y %H:%M UTC")

    summary = ai_summary("\n".join(news))

    block = "\n".join(news)

    return f"""
🌊 STRETTO DI HORMUZ — OSINT REPORT

📅 {now}

🧠 RIASSUNTO AI (GRATIS):
{summary}

📰 FONTI:
{block}
"""

# ================= CHAT =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.lower()

    news = fetch_news()

    context_text = "\n".join(news)

    response = ai_summary(f"{user_text}\n\nCONTESTO:\n{context_text}")

    await update.message.reply_text(response)

# ================= AUTO REPORT =================
async def send_update():
    global last_report

    news = fetch_news()
    report = format_report(news)

    # evita spam
    if report == last_report:
        return

    last_report = report

    await bot_app.bot.send_message(chat_id=CHAT_ID, text=report)

# ================= START =================
async def main():
    global bot_app

    bot_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(send_update()), "interval", minutes=5)
    scheduler.start()

    await send_update()

    print("Bot AI GRATIS attivo")

    await bot_app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
