🌸 Shizuku + YouTube Downloader Bot

A Telegram bot that combines Shizuku-inspired AFK & info features with a powerful YouTube video/audio downloader. Built with Pyrogram and yt-dlp, ready to run on Termux or any Python environment.


---

🔹 Features

AFK & Info (Shizuku Style)

/afk [reason] → Set your AFK status with an optional reason.

/ping → Check if the bot is alive.

/info → Get your username & full name.

/id → Get your Telegram user ID.

/chatinfo → Get info about the current chat/group.


YouTube Downloader

Send any YouTube link to the bot.

Select type: Video 🎥 or Audio 🎵.

Select format: MP4/WEBM for video, MP3/M4A for audio.

Select quality/bitrate.

Bot downloads and sends the file directly in Telegram.



---

🔹 Demo Screenshots

(Replace with your own images if available)




---

🔹 Installation

Requirements

Python 3.11+

Termux or Linux/Windows/macOS

Telegram Bot Token

API_ID & API_HASH from my.telegram.org



---

Step 1: Clone the Repo

git clone https://github.com/<your-username>/Shizuku-YT-Downloader-Bot.git
cd Shizuku-YT-Downloader-Bot

Step 2: Install Dependencies

pip install -r requirements.txt

Step 3: Create .env File

API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token

Step 4: Run the Bot

python bot.py


---

🔹 Usage

AFK & Info Commands

Command	Description

/afk [reason]	Set your AFK with optional reason
/ping	Test if bot is online
/info	Get your username & full name
/id	Get your user ID
/chatinfo	Get current chat/group info
/help	Show all commands


YouTube Download

1. Send any YouTube link to the bot.


2. Select type (Video/Audio).


3. Select format (MP4/WEBM or MP3/M4A).


4. Select quality/bitrate.


5. Bot downloads & sends the file.




---

🔹 Notes

Video files are sent as documents; audio files as audio messages.

AFK database is stored in afk.db.

Temporary YouTube downloads are auto-deleted after sending.

Recommended for private or small group use due to file size limits in Telegram.



---

🔹 Contributing

Fork the repository.

Make your changes.

Submit a pull request with clear description.



---

🔹 License

This project is MIT Licensed – free to use, modify, and share.

