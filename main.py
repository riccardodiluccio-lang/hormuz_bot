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
seen_news = set()

# ================= RSS =================
RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://news.google.com/rss/search?q=Strait+of+Hormuz",
    "https://news.google.com/rss/search?q=Iran+oil"
]

KEYWORDS = ["hormuz", "iran", "oil", "shipping", "strait", "middle east"]

# ================= FETCH NEWS (NO DUPLICATI) =================
def fetch_news():
    global seen_news

    news = []

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)

        for entry in feed.entries[:10]:
            title = entry.title.strip()
            link = getattr(entry, "link", "")

            news_id = title.lower()

            if any(k in news_id for k in KEYWORDS):
                if news_id not in seen_news:
                    seen_news.add(news_id)
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

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json={"inputs": f"Riassumi in italiano: {text}"},
            timeout=20
        )

        data = response.json()

        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"]

        return "Riassunto non disponibile (ma news ricevute)."

    except:
        return "Errore AI, ma news disponibili."

# ================= FORMAT REPORT =================
def format_report(news):
    now = datetime.now().strftime("%d/%m/%Y %H:%M UTC")

    summary = ai_summary("\n".join(news))

    block = "\n".join(news) if news else "Nessuna nuova notizia."

    return f"""
🌊 STRETTO DI HORMUZ — OSINT REPORT

📅 {now}

🧠 RIASSUNTO AI (GRATIS):
{summary}

📰 NOTIZIE:
{block}
"""

# ================= CHAT BOT =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.lower()

    news = fetch_news()

    context_text = "\n".join(news)

    answer = ai_summary(f"Domanda: {user_text}\n\nContesto:\n{context_text}")

    await update.message.reply_text(answer)

# ================= AUTO REPORT =================
async def send_update():
    global last_report

    news = fetch_news()
    report = format_report(news)

    # ❌ blocco duplicati messaggio
    if report == last_report:
        return

    last_report = report

    await bot_app.bot.send_message(chat_id=CHAT_ID, text=report)

# ================= START BOT =================
async def main():
    global bot_app

    bot_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(send_update()), "interval", minutes=5)
    scheduler.start()

    await send_update()

    print("Bot attivo e stabile")

    await bot_app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
