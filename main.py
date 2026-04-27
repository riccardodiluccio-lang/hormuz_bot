import os
import requests
import asyncio
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
HORMUZ_API_URL = os.getenv("HORMUZ_API_URL", "https://api.hormuzmonitor.com/v2")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("Devi impostare TELEGRAM_TOKEN e CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

def get_hormuz_data():
    try:
        risk = requests.get(f"{HORMUZ_API_URL}/risk", timeout=10).json()
        traffic = requests.get(f"{HORMUZ_API_URL}/traffic", timeout=10).json()
        crisis = requests.get(f"{HORMUZ_API_URL}/crisis", timeout=10).json()
        prices = requests.get(f"{HORMUZ_API_URL}/prices", timeout=10).json()
        return risk, traffic, crisis, prices
    except:
        return None, None, None, None

def format_report(risk, traffic, crisis, prices):
    if not all([risk, traffic, crisis, prices]):
        return "⚠️ Errore recupero dati"

    r = risk.get("data", {})
    return f"🌊 Hormuz Update\nRischio: {r.get('risk_score')}"

async def send_update():
    risk, traffic, crisis, prices = get_hormuz_data()
    message = format_report(risk, traffic, crisis, prices)

    await bot.send_message(chat_id=CHAT_ID, text=message)

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_update, 'interval', minutes=15)
    scheduler.start()

    await send_update()

    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
