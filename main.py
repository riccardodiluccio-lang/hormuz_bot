import os
import asyncio
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

# === CONFIGURAZIONE ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("Devi impostare TELEGRAM_TOKEN e CHAT_ID nelle variables di Railway")

bot = Bot(token=TELEGRAM_TOKEN)

# === FALSO DATA LOADER (API DISATTIVATA) ===
def get_hormuz_data():
    return None, None, None, None

# === MESSAGGIO STABILE ===
def format_report(risk, traffic, crisis, prices):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    return f"""
🌊 **STRETTO DI HORMUZ — MONITOR**

📅 {now} UTC

⚠️ Sistema in modalità stabile
📡 Dati esterni non disponibili

🟢 Bot attivo su Railway
🤖 Monitoraggio automatico ogni 15 minuti

🔗 Sistema operativo
"""

# === INVIO TELEGRAM ===
async def send_update():
    message = format_report(None, None, None, None)

    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode="Markdown"
        )
        print("Messaggio inviato")
    except Exception as e:
        print(f"Errore invio: {e}")

# === MAIN LOOP ===
async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_update, 'interval', minutes=15)
    scheduler.start()

    print("Bot avviato su Railway")

    await send_update()

    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
