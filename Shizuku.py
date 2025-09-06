import sqlite3
import random
from datetime import datetime
from pyrogram import filters
from pyrogram.types import Message
from bot import app   # ✅ import main app

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

# ================== COMMANDS ==================

@app.on_message(filters.command("start"))
async def start(_, m: Message):
    caption = (
        "🌸 Welcome to Shizuku AFK Bot! 🌸\n\n"
        "Inspired by Shizuku from Hunter x Hunter, this bot brings her calm and mysterious vibe into your group. "
        "Whether you’re going AFK, setting a reason, or just want to keep things neat and stylish, "
        "Shizuku’s got you covered. Simple, elegant, and always reliable — just like her! ✨"
    )
    await m.reply_photo(
        photo="https://files.catbox.moe/dobeog.jpg",
        caption=caption
    )

@app.on_message(filters.command("help"))
async def help_cmd(_, m: Message):
    caption = (
        "🌸 Shizuku AFK Bot Help Menu 🌸\n\n"
        "Available Commands:\n"
        "/afk [reason] → Set your AFK with an optional reason.\n"
        "/ping → Test if the bot is alive.\n"
        "/info → Get your username and full name.\n"
        "/id → Get your user ID.\n"
        "/chatinfo → Get current chat/group info and ID.\n"
        "/help → Show this help menu."
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

@app.on_message(filters.command("info"))
async def info_handler(_, m: Message):
    user = m.from_user
    response = f"👤 User Info:\n" \
               f"Name: {user.first_name} {user.last_name or ''}\n" \
               f"Username: @{user.username or 'N/A'}"
    await m.reply(response)

@app.on_message(filters.command("id"))
async def id_handler(_, m: Message):
    user = m.from_user
    await m.reply(f"🆔 User ID: `{user.id}`")

@app.on_message(filters.command("chatinfo"))
async def chatinfo_handler(_, m: Message):
    chat = m.chat
    response = f"🏠 Chat Info:\n" \
               f"Title: {chat.title}\n" \
               f"Type: {chat.type}\n" \
               f"Chat ID: `{chat.id}`"
    await m.reply(response)

# ================== AFK HANDLER ==================
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

    target = None
    if m.reply_to_message and m.reply_to_message.from_user:
        target = m.reply_to_message.from_user.id

    if target:
        afk_data = get_afk(target)
        if afk_data:
            afk_time = format_afk_time(afk_data[1])
            reason = afk_data[2] if afk_data[2] else random.choice(SHIZUKU_QUOTES)
            await m.reply_text(
                f"😴🎀 {m.reply_to_message.from_user.mention} is AFK.\n"
                f"⏳ AFK: {afk_time}\n"
                f"📋 Reason: {reason}"
            )
            update_count(target, is_sticker=m.sticker is not None)