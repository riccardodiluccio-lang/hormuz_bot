import os
import asyncio
import feedparser
import hashlib
from datetime import datetime
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ================= CONFIG =================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# ================= STATE =================
seen_news = set()
collected_news = []

# ================= RSS (GLOBAL AGGREGATOR) =================
RSS_URL = "https://news.google.com/rss/search?q=Strait+of+Hormuz+OR+Iran+oil+shipping&hl=en&gl=US&ceid=US:en"

# ================= FETCH NEWS =================
def fetch_news():
    global seen_news, collected_news

    feed = feedparser.parse(RSS_URL)

    for entry in feed.entries:
        title = entry.title.strip()
        link = entry.link

        # crea ID unico
        news_id = hashlib.md5(title.encode()).hexdigest()

        if news_id not in seen_news:
            seen_news.add(news_id)

            collected_news.append({
                "title": title,
                "link": link
            })

# ================= SIMPLE AI SUMMARY (NO API) =================
def summarize_news(news):
    if not news:
        return "Nessun aggiornamento rilevante nelle ultime ore."

    # prendi max 10 notizie più recenti
    recent = news[-10:]

    keywords = {
        "iran": 0,
        "oil": 0,
        "shipping": 0,
        "military": 0,
        "attack": 0
    }

    for n in recent:
        text = n["title"].lower()
        for k in keywords:
            if k in text:
                keywords[k] += 1

    livello = "🟢 BASSO"
    if sum(keywords.values()) > 10:
        livello = "🔴 ALTO"
    elif sum(keywords.values()) > 5:
        livello = "🟡 MEDIO"

    return f"""
Livello attività: {livello}

Segnali rilevati:
{', '.join([f"{k}:{v}" for k,v in keywords.items() if v > 0])}

Sintesi:
Le notizie indicano un'attività monitorata nella regione dello Stretto di Hormuz, con aggiornamenti da fonti internazionali.
"""

# ================= FORMAT =================
def format_report():
    global collected_news

    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    if not collected_news:
        return "Nessuna nuova notizia disponibile."

    summary = summarize_news(collected_news)

    # prendi ultime 10
    recent = collected_news[-10:]

    news_text = ""
    for n in recent:
        news_text += f"📰 {n['title']}\n🔗 {n['link']}\n\n"

    return f"""
🌊 STRETTO DI HORMUZ — REPORT

📅 {now}

====================
🧠 RIASSUNTO
====================
{summary}

====================
📰 NOTIZIE
====================
{news_text}
"""

# ================= JOB OGNI MINUTO =================
async def collect_job():
    fetch_news()

# ================= INVIO OGNI 15 MIN =================
async def send_job():
    global collected_news

    if not collected_news:
        return

    report = format_report()

    await bot.send_message(
        chat_id=CHAT_ID,
        text=report
    )

    # svuota dopo invio (evita duplicati futuri)
    collected_news = []

# ================= MAIN =================
async def main():
    scheduler = AsyncIOScheduler()

    # ogni minuto raccoglie news
    scheduler.add_job(collect_job, "interval", minutes=1)

    # ogni 15 min manda report
    scheduler.add_job(send_job, "interval", minutes=1)

    scheduler.start()

    print("Bot stabile avviato")

    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
