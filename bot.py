import os
from pyrogram import Client, filters
from pyrogram.types import Message
import yt_dlp

# Credentials
API_ID = 31526501
API_HASH = "cf2792e0bcbdb620a31dd65a43f88c8a"
BOT_TOKEN = "8419613072:AAHy1x_3eJOvjp5l-gAgMiJTtkrS5X84niA"

# Download directory setup
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

app = Client("video_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply_text("ကျွန်တော့နာမည် အောင်အောင်ဦး ပါ! ဗီဒီယိုလင့်ခ် ပို့ပေးပါ၊ ဒေါင်းလုဒ်လုပ်ပေးပါမယ်။")

@app.on_message(filters.text & ~filters.command("start"))
async def download_video(client, message: Message):
    url = message.text.strip()
    
    # Link Verification
    if not (url.startswith("http://") or url.startswith("https://")):
        await message.reply_text("❌ ဗီဒီယိုလင့်ခ် သာ ပို့ပေးပါ။")
        return

    status_msg = await message.reply_text("⏳ ဗီဒီယိုကို ဒေါင်းလုဒ်လုပ်နေပါပြီ...")
    
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'format': 'best[ext=mp4]/best',
        'noplaylist': True,
        'quiet': True
    }
    
    file_path = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        await status_msg.edit_text("📤 Telegram သို့ တင်ပေးနေပါပြီ...")
        await message.reply_video(video=file_path, caption=info.get('title', 'Video'))
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ ဒေါင်းလုဒ်ဆွဲရာတွင် အမှားအယွင်းရှိပါသည်: {str(e)[:100]}")
    finally:
        # Cleanup downloads folder
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

if __name__ == "__main__":
    app.run()
