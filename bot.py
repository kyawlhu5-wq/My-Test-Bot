import os
from pyrogram import Client, filters
from pyrogram.types import Message
import yt_dlp

# ဆရာ့ရဲ့ အချက်အလက်များကို ထည့်သွင်းပြီးပါပြီ
API_ID = 31526501
API_HASH = "cf2792e0bcbdb620a31dd65a43f88c8a"
BOT_TOKEN = "8419613072:AAF5bnkg3ld__mY0uHiYA1-wYNeE07UcIk4"

app = Client("video_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply_text("ကျွန်တော့နာမည် အောင်အောင်ဦး ပါ!/ ဗီဒီယိုလင့်ခ် ပို့ပေးပါ၊ ဒေါင်းလုဒ်လုပ်ပေးပါမယ်။")

@app.on_message(filters.text & ~filters.command("start"))
async def download_video(client, message: Message):
    url = message.text
    if not url.startswith("http"):
        await message.reply_text("❌ video link ပဲပို့ပေးဟ လီးပဲ။")
        return

    status_msg = await message.reply_text("⏳ ဗီဒီယိုကို ဒေါင်းလုဒ်လုပ်နေပါပြီ၊ စောင့်ချင်စောင့် မစောင့်ချင်နေ...")
    ydl_opts = {'outtmpl': 'downloads/%(id)s.%(ext)s', 'format': 'best[ext=mp4]/best', 'noplaylist': True}
    file_path = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        await status_msg.edit_text("📤 Telegram ဆီ တင်ပေးနေတယ် ခနစောင့်...")
        await message.reply_video(video=file_path, caption=info.get('title', 'Video'))
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ ဘာတွေလာပို့နေတာလဲ လီးလား: {e}")
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    print("ကြောင်Botလေး စတင်အလုပ်လုပ်နေပါပြီ...")
    app.run()
