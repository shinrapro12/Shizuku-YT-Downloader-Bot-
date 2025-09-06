import os
from pyrogram import Client
from dotenv import load_dotenv

# Load config.env
load_dotenv("config.env")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Main Pyrogram Client
app = Client(
    "shizuku_yt_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Import features (handlers will attach to app)
import Shizuku
import YouTube

print("✅ Shizuku + YouTube Bot is running...")
app.run()