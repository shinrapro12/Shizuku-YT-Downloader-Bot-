import os
import asyncio
import uuid
import re
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from yt_dlp import YoutubeDL
from tempfile import TemporaryDirectory
from bot import bot   # use the shared bot client

# --- Temporary storage ---
url_store = {}        # short_id -> URL
user_choices = {}     # short_id -> user selections
last_percent_map = {} # query.id -> last percent


# --- Handle YouTube links ---
@bot.on_message(filters.regex(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/"))
async def youtube_link(client, message):
    url = message.text.strip()
    short_id = str(uuid.uuid4())[:8]
    url_store[short_id] = url
    user_choices[short_id] = {}

    # Step 1: Audio or Video
    await message.reply_text(
        "Select type to download:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎥 Video", callback_data=f"type|video|{short_id}")],
            [InlineKeyboardButton("🎵 Audio", callback_data=f"type|audio|{short_id}")]
        ])
    )


# --- Callback query handler ---
@bot.on_callback_query()
async def callback_handler(client, query: CallbackQuery):
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

        # Step 2: Format selection
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

        # Step 3: Show quality options
        with YoutubeDL({}) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])

        keyboard = []

        if media_type == "video":
            seen = set()
            for f in sorted(formats, key=lambda x: int(x.get("height") or 0)):
                if f.get("vcodec") == "none" or f.get("ext") != file_format:
                    continue
                res = f.get("height")
                if not res:
                    continue
                res_key = f"{res}-{f.get('ext')}-{f.get('vcodec')}"
                if res_key in seen:
                    continue
                seen.add(res_key)
                kb_text = f"{res}p"
                keyboard.append([InlineKeyboardButton(kb_text, callback_data=f"download|{f['format_id']}|{short_id}")])

        else:  # audio
            seen = set()
            for f in sorted(formats, key=lambda x: int(x.get("abr") or 0)):
                if f.get("acodec") == "none" or f.get("vcodec") != "none":
                    continue
                if file_format != f.get("ext"):
                    continue
                abr = f.get("abr")
                if not abr:
                    continue
                abr_key = f"{abr}-{f.get('ext')}-{f.get('acodec')}"
                if abr_key in seen:
                    continue
                seen.add(abr_key)
                kb_text = f"{abr}kbps"
                keyboard.append([InlineKeyboardButton(kb_text, callback_data=f"download|{f['format_id']}|{short_id}")])

        await query.message.edit_text(
            "Select quality:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # Step 3: Download selected
    elif data.startswith("download|"):
        _, format_id, short_id = data.split("|")
        url = url_store.get(short_id)
        if not url:
            await query.answer("❌ URL expired!")
            return

        media_type = user_choices[short_id]['type']
        await query.answer("Starting download 😁")
        await download_and_send(query, url, format_id, media_type)


# --- Download & send file ---
async def download_and_send(query, url, format_id, media_type):
    try:
        with TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "%(title)s.%(ext)s")

            if media_type == "video":
                ydl_opts = {
                    "format": f"{format_id}+bestaudio/best",
                    "outtmpl": filename,
                    "merge_output_format": "mp4",
                    "progress_hooks": [lambda d: asyncio.create_task(update_progress(query, d))]
                }
            else:
                ydl_opts = {
                    "format": format_id,
                    "outtmpl": filename,
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


# --- Optimized Progress bar ---
async def update_progress(query, d):
    key = query.id

    if d['status'] == 'downloading':
        percent_str = d.get('_percent_str', '0%')
        percent_clean = re.sub(r'\x1b\[[0-9;]*m', '', percent_str)
        try:
            percent = float(percent_clean.replace('%','').strip())
        except:
            percent = 0.0

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