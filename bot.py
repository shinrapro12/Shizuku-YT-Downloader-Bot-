import os
import asyncio
import uuid
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from yt_dlp import YoutubeDL
from tempfile import TemporaryDirectory
from dotenv import load_dotenv

# --- Load config from config.env ---
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Client(
    "Shizuku_YT_AFK_Bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# --- AFK Storage ---
afk_users = {}

# --- YouTube Temporary Storage ---
url_store = {}
user_choices = {}

# ================== BOT COMMANDS ==================

# --- /start ---
@bot.on_message(filters.command("start"))
async def start_cmd(client, message: Message):
    await message.reply_text(
        "🌸 Welcome to **Shizuku AFK Bot!** 🌸\n\n"
        "Inspired by Shizuku from *Hunter x Hunter*, this bot brings her calm and mysterious vibe into your group.\n\n"
        "Whether you’re going AFK, setting a reason, or just want to keep things neat and stylish, Shizuku’s got you covered.\n\n"
        "✨ Simple, elegant, and always reliable — just like her!"
    )

# --- /afk ---
@bot.on_message(filters.command("afk"))
async def set_afk(client, message: Message):
    reason = " ".join(message.command[1:]) if len(message.command) > 1 else "AFK"
    afk_users[message.from_user.id] = reason
    await message.reply_text(f"🌙 {message.from_user.first_name} is now AFK: `{reason}`")

# --- Remove AFK when user sends a message ---
@bot.on_message(filters.all & ~filters.command("afk"))
async def remove_afk(client, message: Message):
    if message.from_user and message.from_user.id in afk_users:
        afk_users.pop(message.from_user.id, None)
        await message.reply_text(f"💤 Welcome back, {message.from_user.first_name}! AFK removed.")

# --- If someone mentions AFK user ---
@bot.on_message(filters.text & filters.group)
async def mention_afk(client, message: Message):
    if message.reply_to_message and message.reply_to_message.from_user.id in afk_users:
        reason = afk_users[message.reply_to_message.from_user.id]
        await message.reply_text(f"⏳ That user is AFK: `{reason}`")

# --- /id ---
@bot.on_message(filters.command("id"))
async def get_id(client, message: Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        await message.reply_text(f"🆔 **User ID:**\n`{user_id}`")
    else:
        user_id = message.from_user.id
        await message.reply_text(f"🆔 **Your ID:**\n`{user_id}`")

# --- /chatinfo ---
@bot.on_message(filters.command("chatinfo"))
async def chat_info(client, message: Message):
    chat = message.chat
    await message.reply_text(
        f"💬 **Chat Info**\n\n"
        f"🆔 Chat ID: `{chat.id}`\n"
        f"📛 Title: {chat.title or 'N/A'}\n"
        f"👥 Type: {chat.type}"
    )

# ================== YOUTUBE DOWNLOADER ==================

# --- Handle YouTube links ---
@bot.on_message(filters.regex(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/"))
async def youtube_link(client, message: Message):
    url = message.text.strip()
    short_id = str(uuid.uuid4())[:8]
    url_store[short_id] = url
    user_choices[short_id] = {}

    await message.reply_text(
        "Select type to download:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎥 Video", callback_data=f"type|video|{short_id}")],
            [InlineKeyboardButton("🎵 Audio", callback_data=f"type|audio|{short_id}")]
        ])
    )

# --- Callback Handler ---
@bot.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    data = query.data

    # Step 1: Select type
    if data.startswith("type|"):
        _, media_type, short_id = data.split("|")
        url = url_store.get(short_id)
        if not url:
            await query.answer("❌ URL expired!")
            return

        user_choices[short_id]['type'] = media_type
        await query.answer(f"{media_type.capitalize()} selected 😁")

        if media_type == "video":
            keyboard = [
                [InlineKeyboardButton("MP4", callback_data=f"format|mp4|{short_id}")],
                [InlineKeyboardButton("WEBM", callback_data=f"format|webm|{short_id}")]
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("MP3", callback_data=f"format|mp3|{short_id}")],
                [InlineKeyboardButton("M4A", callback_data=f"format|m4a|{short_id}")]
            ]
        await query.message.edit_text("Select format:", reply_markup=InlineKeyboardMarkup(keyboard))

    # Step 2: Select format
    elif data.startswith("format|"):
        _, file_format, short_id = data.split("|")
        url = url_store.get(short_id)
        if not url:
            await query.answer("❌ URL expired!")
            return

        user_choices[short_id]['format'] = file_format
        media_type = user_choices[short_id]['type']
        await query.answer(f"{file_format.upper()} selected 😁")

        # Just download best available (simplified for Termux stability)
        await query.message.edit_text("⏳ Downloading, please wait...")
        await download_and_send(query, url, media_type, file_format)

# --- Download & Send ---
async def download_and_send(query, url, media_type, file_format):
    try:
        with TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "%(title)s.%(ext)s")

            ydl_opts = {
                "format": "bestvideo+bestaudio/best" if media_type == "video" else "bestaudio/best",
                "outtmpl": filename,
                "merge_output_format": file_format if media_type == "video" else None
            }

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            for file in os.listdir(tmpdir):
                file_path = os.path.join(tmpdir, file)
                if media_type == "audio":
                    await query.message.reply_audio(file_path, title=os.path.splitext(file)[0])
                else:
                    await query.message.reply_document(file_path)

            await query.message.edit_text("✅ Download Complete 🎉")

    except Exception as e:
        await query.message.reply_text(f"❌ Error: {e}")

# ================== RUN BOT ==================
bot.run()