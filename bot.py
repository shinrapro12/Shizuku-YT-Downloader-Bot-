from pyrogram import Client
from dotenv import load_dotenv
import os

# Load credentials from config.env
load_dotenv("config.env")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Client(
    "ShizukuYTBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Import handlers
import shizuku
import youtube

print("✅ Shizuku + YouTube Downloader Bot Started...")
bot.run()