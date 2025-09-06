import os
from pyrogram import Client
from dotenv import load_dotenv

# Load environment variables from config.env
load_dotenv("config.env")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- Main Pyrogram Client ---
bot = Client(
    "Shizuku_YT_Bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ✅ Import handlers AFTER bot is created
import Shizuku
import YouTube

if __name__ == "__main__":
    print("✅ Shizuku + YouTube Bot is running...")
    bot.run()