import os
import sqlite3
import random
import uuid
import re
import asyncio
from datetime import datetime
from tempfile import TemporaryDirectory

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from yt_dlp import YoutubeDL
from dotenv import load_dotenv

# ================== LOAD CONFIG ==================
load_dotenv("config.env")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ================== INIT BOT ==================
app = Client("shizuku_yt_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ================== DATABASE ==================
conn = sqlite3.connect("afk.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS afk (
    user_id INTEGER,
    since TEXT,
    reason TEXT,
    is_afk INTEGER,
    msg_count INTEGER,
    sticker_count INTEGER
)
""")
conn.commit()

# ================== QUOTES ==================
SHIZUKU_QUOTES = [
    "🌸 Silence is also an answer.",
    "🌸 Even in chaos, there is beauty.",
    "🌸 Simplicity is the ultimate sophistication.",
    "🌸 Calmness is strength."
]

# ================== UTILS ==================
def set_afk(user_id, reason=None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("DELETE FROM afk WHERE user_id=?", (user_id,))
    cursor.execute("INSERT INTO afk VALUES (?, ?, ?, ?, ?, ?)",
                   (user_id, now, reason, 1, 0, 0))
    conn.commit()

def remove_afk(user_id):
    cursor.execute("DELETE FROM afk WHERE user_id=?", (user_id,))
    conn.commit()

def get_afk(user_id):
    cursor.execute("SELECT * FROM afk WHERE user_id=?", (user_id,))
    return cursor.fetchone()

def update_count(user_id, is_sticker=False):
    if is_sticker:
        cursor.execute("UPDATE afk SET sticker_count = sticker_count + 1 WHERE user_id=?", (user_id,))
    else:
        cursor.execute("UPDATE afk SET msg_count = msg_count + 1 WHERE user_id=?", (user_id,))
    conn.commit()

def format_afk_time(start_time):
    since = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    delta = datetime.now() - since
    days, seconds = delta.days, delta.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    sec = seconds % 60
    if days > 0:
        return f"{days}d {hours}h {minutes}m {sec}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {sec}s"
    elif minutes > 0:
        return f"{minutes}m {sec}s"
    else:
        return f"{sec}s"

# ================== AFK & INFO COMMANDS ==================

@app.on_message(filters.command("start"))
async def start_cmd(_, m: Message):
    caption = (
        "🌸 Welcome to Shizuku + YouTube Downloader Bot! 🌸\n\n"
        "AFK, info, and YouTube video/audio downloads all in one bot. ✨"
    )
    await m.reply_photo(
        photo="https://files.catbox.moe/dobeog.jpg",
        caption=caption
    )

@app.on_message(filters.command("help"))
async def help_cmd(_, m: Message):
    caption = (
        "🌸 Help Menu 🌸\n\n"
        "AFK Commands:\n"
        "/afk [reason] → Set AFK with optional reason\n"
        "/ping → Test if bot is alive\n"
        "/info → Get username & full name\n"
        "/id → Get user ID\n"
        "/chatinfo → Get chat/group info\n\n"
        "YouTube Commands:\n"
        "Send any YouTube link → Select video/audio, format & quality to download"
    )
    await m.reply_photo(
        photo="https://files.catbox.moe/jlp7hd.jpg",
        caption=caption
    )

@app.on_message(filters.command("ping"))
async def ping(_, m: Message):
    now = datetime.now().strftime("%A, %d %B %Y | %H:%M:%S")
    await m.reply_text(f"🏓 Pong!\n📅 {now}")

@app.on_message(filters.command("afk"))
async def afk_set(_, m: Message):
    reason = m.text.split(" ", 1)[1] if len(m.text.split()) > 1 else None
    set_afk(m.from_user.id, reason)
    if reason:
        await m.reply_text(f"😴 {m.from_user.mention} is now AFK.\n📋 Reason: {reason}")
    else:
        await m.reply_text(f"😴 {m.from_user.mention} is now AFK.\n{random.choice(SHIZUKU_QUOTES)}")

@app.on_message(filters.command("info") & (filters.private | filters.group))
async def info_handler(client: Client, message: Message):
    user = message.from_user
    response = f"👤 User Info:\n" \
               f"Name: {user.first_name} {user.last_name or ''}\n" \
               f"Username: @{user.username or 'N/A'}"
    await message.reply(response)

@app.on_message(filters.command("id") & (filters.private | filters.group))
async def id_handler(client: Client, message: Message):
    user = message.from_user
    await message.reply(f"🆔 User ID: {user.id}")

@app.on_message(filters.command("chatinfo") & (filters.group | filters.channel))
async def chatinfo_handler(client: Client, message: Message):
    chat = message.chat
    response = f"🏠 Chat Info:\n" \
               f"Title: {chat.title}\n" \
               f"Type: {chat.type}\n" \
               f"Chat ID: {chat.id}"
    await message.reply(response)

@app.on_message(~filters.command(["afk", "start", "help", "ping", "info", "id", "chatinfo"]))
async def afk_handler(_, m: Message):
    if not m.from_user:
        return

    afk_data = get_afk(m.from_user.id)
    if afk_data:
        afk_time = format_afk_time(afk_data[1])
        reason = afk_data[2] if afk_data[2] else random.choice(SHIZUKU_QUOTES)
        await m.reply_text(
            f"🕊 Welcome back {m.from_user.mention}\n"
            f"⏳ AFK: {afk_time}\n"
            f"📋 Reason: {reason}"
        )
        remove_afk(m.from_user.id)
        return

    # Notify if someone tags or replies to an AFK user
    target = None
    if m.reply_to_message and m.reply_to_message.from_user:
        target = m.reply_to_message.from_user.id
    elif m.entities:
        for entity in m.entities:
            if entity.type == "mention" and "@" in m.text:
                username = m.text.split("@")[1].split()[0]
                try:
                    user = await app.get_users(username)
                    target = user.id
                    break
                except:
                    pass

    if target:
        afk_data = get_afk(target)
        if afk_data:
            afk_time = format_afk_time(afk_data[1])
            reason = afk_data[2] if afk_data[2] else random.choice(SHIZUKU_QUOTES)
            await m.reply_text(
                f"😴 {m.reply_to_message.from_user.mention if m.reply_to_message else '@'+username} is AFK.\n"
                f"⏳ AFK: {afk_time}\n"
                f"📋 Reason: {reason}"
            )
            update_count(target, is_sticker=m.sticker is not None)

# ================== YOUTUBE DOWNLOADER ==================

url_store = {}        # short_id -> URL
user_choices = {}     # short_id -> user selections
last_percent_map = {} # query.id -> last percent

@app.on_message(filters.regex(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/"))
async def youtube_link(client, message):
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

@app.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    data = query.data

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
        await query.message.edit_text(
            "Select format:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("format|"):
        _, file_format, short_id = data.split("|")
        url = url_store.get(short_id)
        if not url:
            await query.answer("❌ URL expired!")
            return

        user_choices[short_id]['format'] = file_format
        media_type = user_choices[short_id]['type']
        await query.answer(f"{file_format.upper()} selected 😁")

        with YoutubeDL({}) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])

        keyboard = []

        if media_type == "video":
            seen_res = set()
            for f in sorted(formats, key=lambda x: int(x.get("height") or 0)):
                if f.get("vcodec") == "none" or f.get("ext") != file_format:
                    continue
                res = f.get("height")
                if not res or res in seen_res:
                    continue
                seen_res.add(res)
                kb_text = f"{res}p"
                keyboard.append([InlineKeyboardButton(kb_text, callback_data=f"download|{f['format_id']}|{short_id}")])
        else:
            seen_bitrate = set()
            for f in sorted(formats, key=lambda x: int(x.get("abr") or 0)):
                if f.get("acodec") == "none" or f.get("vcodec") != "none":
                    continue
                if file_format == "mp3" and f.get("ext") != "mp3":
                    continue
                if file_format == "m4a" and f.get("ext") != "m4a":
                    continue
                abr = f.get("abr")
                if abr in seen_bitrate:
                    continue
                seen_bitrate.add(abr)
                kb_text = f"{abr}kbps"
                keyboard.append([InlineKeyboardButton(kb_text, callback_data=f"download|{f['format_id']}|{short_id}")])

        await query.message.edit_text(
            "Select quality:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("download|"):
        _, format_id, short_id = data.split("|")
        url = url_store.get(short_id)
        if not url:
            await query.answer("❌ URL expired!")
            return
        media_type = user_choices[short_id]['type']
        await query.answer("Starting download 😁")
        await download_and_send(query, url, format_id, media_type)

async def download_and_send(query, url, format_id, media_type):
    try:
        with TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "%(title)s.%(ext)s")
            
            ydl_opts = {
                "format": f"{format_id}+bestaudio/best" if media_type=="video" else format_id,
                "outtmpl": filename,
                "merge_output_format": "mp4" if media_type=="video" else None,
                "progress_hooks": [lambda d: asyncio.create_task(update_progress(query, d))]
            }

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            for file in os.listdir(tmpdir):
                file_path = os.path.join(tmpdir, file)
                if media_type == "audio":
                    await query.message.reply_audio(file_path, title=os.path.splitext(file)[0])
                else:
                    await query.message.reply_document(file_path)
    except Exception as e:
        await query.message.reply_text(f"❌ Error: {e}")

async def update_progress(query, d):
    key = query.id
    if d['status'] == 'downloading':
        percent_str = d.get('_percent_str', '0%')
        percent_clean = re.sub(r'\x1b\[[0-9;]*m', '', percent_str)
        percent = float(percent_clean.replace('%','').strip())
        last_percent = last_percent_map.get(key, -1)
        if abs(percent - last_percent) < 2:
            return
        last_percent_map[key] = percent
        total_blocks = 20
        filled = int(percent / 100 * total_blocks)
        bar = '▓' * filled + '░' * (total_blocks - filled)
        if query.message:
            await query.message.edit(f"😁 Downloading… [{bar}] {int(percent)}%")
    elif d['status'] == 'finished':
        if query.message:
            await query.message.edit("😁 Download Complete 🎉")
        if key in last_percent_map:
            del last_percent_map[key]

# ================== RUN BOT ==================
print("✅ Shizuku + YouTube Downloader Bot Started...")
app.run()