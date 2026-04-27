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
            link = getattr(entry, "link", "no source")

            if any(k in title.lower() for k in KEYWORDS):
                news.append({"title": title, "link": link})

    return news[:15]

# ================= “AI” SUMMARY IN ITALIAN =================
def summarize_it(news):
    if not news:
        return "Non ci sono sviluppi rilevanti al momento."

    if len(news) < 3:
        stato = "🟢 Attività bassa nella regione"
    elif len(news) < 7:
        stato = "🟡 Attività moderata e segnali geopolitici in evoluzione"
    else:
        stato = "🔴 Alta intensità informativa e possibili tensioni in aumento"

    keywords = {}
    for n in news:
        text = n["title"].lower()
        for k in ["iran", "oil", "shipping", "usa", "strait"]:
            if k in text:
                keywords[k] = keywords.get(k, 0) + 1

    segnali = ", ".join([f"{k}:{v}" for k, v in keywords.items()]) if keywords else "nessun segnale dominante"

    return f"""
{stato}

📊 Analisi segnali:
{segnali}

🧠 Interpretazione:
Il sistema sta monitorando flussi di notizie globali.
Non ci sono conferme ufficiali di eventi critici in corso.
"""

# ================= FORMAT MESSAGE =================
def format_message(news):
    now = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")

    summary = summarize_it(news)

    block = ""
    for n in news[:10]:
        block += f"📰 {n['title']}\n🔗 {n['link']}\n\n"

    return f"""
🌊 STRETTO DI HORMUZ — RAPPORTO INTELLIGENCE

📅 {now}

====================
🧠 RIASSUNTO AI (ITALIANO)
====================
{summary}

====================
📰 NOTIZIE (FONTE ORIGINALE)
====================
{block if block else "Nessuna notizia rilevante"}

====================
SISTEMA
====================
Monitoraggio automatico attivo via RSS globali
"""

# ================= ALERT DETECTION =================
def detect_reopening(news):
    triggers = ["reopened", "reopen", "resumed", "traffic restored", "blockade lifted"]

    return any(any(t in n["title"].lower() for t in triggers) for n in news)

# ================= SEND =================
async def send_update():
    global alert_mode, alert_counter

    news = fetch_news()

    if detect_reopening(news):
        alert_mode = True
        alert_counter = 15

    if alert_mode:
        msg = f"""
🚨 AGGIORNAMENTO CRITICO — STRETTO DI HORMUZ 🚨

RILEVATO POSSIBILE CAMBIAMENTO NELLE CONDIZIONI MARITTIME

STATO: ALLERTA ATTIVA

MINUTI RIMANENTI: {alert_counter}
"""

        alert_counter -= 1

        if alert_counter <= 0:
            alert_mode = False

        await bot.send_message(chat_id=CHAT_ID, text=msg.upper())

    else:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=format_message(news)
        )

# ================= LOOP =================
async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_update, "interval", minutes=1)
    scheduler.start()

    await send_update()

    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
