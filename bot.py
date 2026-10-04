import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp

# Logging သတ်မှတ်ချက်
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== ✍️ စာသားများကို လိုသလို ပြင်ဆင်နိုင်ပါသည် ====================
MSG_START_WELCOME = "👋 မင်္ဂလာပါဆရာ။ 🔗 YouTube, Facebook, TikTok နဲ့ အခြားလင့်ခ်တစ်ခုခုကို ပို့ပေးပါခင်ဗျာ。"
MSG_INVALID_URL   = "⚠️ ကျေးဇူးပြု၍ မှန်ကန်တဲ့ တရားဝင် လင့်ခ် (URL) တစ်ခုကို ပို့ပေးပါ။"
MSG_CHOICE_PROMPT = "📥 လင့်ခ်ကို လက်ခံရရှိပါပြီ။ ဘယ်လိုပုံစံနဲ့ ဒေါင်းလုပ်ဆွဲလိုပါသလဲဆရာ?"
MSG_DOWNLOADING   = "⏳ ခဏစောင့်ပါဆရာ၊ ဖိုင်ကို ဆာဗာပေါ်သို့ ဒေါင်းလုပ်ဆွဲနေပါပြီ..."
MSG_CONVERTING    = "🔄 အသံဖိုင် (MP3) သို့ ပြောင်းလဲနေပါပြီ၊ ခဏစောင့်ပေးပါ..."
MSG_UPLOADING     = "📤 ဖိုင်ဒေါင်းလုပ်ပြီးပါပြီ။ Telegram သို့ ပို့ဆောင်နေပါပြီခင်ဗျာ..."
MSG_ERROR         = "❌ ဒေါင်းလုပ်ဆွဲရာတွင် အမှားအယွင်း ရှိသွားပါသည်ဆရာ: {error}"
# ====================================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(MSG_START_WELCOME)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith("http"):
        await update.message.reply_text(MSG_INVALID_URL)
        return

    # URL ကို context ထဲမှာ သိမ်းဆည်းခြင်း
    context.user_data['target_url'] = url

    # Inline Keyboard (Video လား၊ MP3 လား ရွေးချယ်ရန်)
    keyboard = [
        [
            InlineKeyboardButton("🎬 ဗီဒီယို (Video)", callback_data="type_video"),
            InlineKeyboardButton("🎵 အသံဖိုင် (MP3)", callback_data="type_audio")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(MSG_CHOICE_PROMPT, reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    url = context.user_data.get('target_url')
    if not url:
        await query.edit_message_text("❌ လင့်ခ် သက်တမ်းကုန်သွားပါပြီ။ ကျေးဇူးပြု၍ လင့်ခ်အသစ် ပြန်ပို့ပေးပါ။")
        return

    download_type = query.data
    os.makedirs('downloads', exist_ok=True)

    if download_type == "type_video":
        status_msg = await query.edit_message_text(MSG_DOWNLOADING)
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'noplaylist': True,
        }
    else:
        status_msg = await query.edit_message_text(MSG_CONVERTING)
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if download_type == "type_audio":
                filename = os.path.splitext(filename)[0] + ".mp3"

        await status_msg.edit_text(MSG_UPLOADING)

        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                if download_type == "type_video":
                    await query.message.reply_video(video=f)
                else:
                    await query.message.reply_audio(audio=f)
            os.remove(filename)
        else:
            raise Exception("ဒေါင်းလုပ်လုပ်ထားသော ဖိုင်ကို ရှာမတွေ့ပါ။")

        await status_msg.delete()

    except Exception as e:
        logger.error(f"Error downloading: {e}")
        try:
            await status_msg.edit_text(MSG_ERROR.format(error=str(e)))
        except:
            await query.message.reply_text(MSG_ERROR.format(error=str(e)))
        if filename and os.path.exists(filename):
            os.remove(filename)

def main():
    # Bot Token အသစ်ကို ထည့်သွင်းပေးထားပါသည်
    TOKEN = "8419613072:AAE18KPeswX2PtMmkDrdjCw-nNoy5p7xrEs"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("🤖 Telegram Downloader Bot အောင်မြင်စွာ စတင်လည်ပတ်နေပါပြီ...")
    # drop_pending_updates=True ဖြင့် အရင်က ပိတ်မိနေသော စာများနှင့် Webhook များကို ရှင်းထုတ်ပေးသည်
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
