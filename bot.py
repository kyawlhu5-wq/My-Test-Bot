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
MSG_CHOICE_PROMPT = "📥 လင့်ခ်ကို လက်ခံရရှိပါပြီ။ လိုချင်တဲ့ အရည်အသွေး (Quality) သို့မဟုတ် MP3 ကို ရွေးချယ်ပါဆရာ -"
MSG_DOWNLOADING   = "⏳ ခဏစောင့်ပါဆရာ၊ ရွေးချယ်ထားသော အရည်အသွေးဖြင့် ဒေါင်းလုပ်ဆွဲနေပါပြီ..."
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

    # Inline Keyboard (ဗီဒီယို အရည်အသွေးမျိုးစုံနှင့် MP3 ရွေးချယ်ရန်)
    keyboard = [
        [
            InlineKeyboardButton("🎬 HD (1080p)", callback_data="qual_1080"),
            InlineKeyboardButton("🎬 SD (720p)", callback_data="qual_720")
        ],
        [
            InlineKeyboardButton("🎬 Low (360p)", callback_data="qual_360"),
            InlineKeyboardButton("🎵 အသံဖိုင် (MP3)", callback_data="qual_mp3")
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

    choice = query.data
    os.makedirs('downloads', exist_ok=True)

    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'noplaylist': True,
    }
    
    is_audio = False

    if choice == "qual_1080":
        ydl_opts['format'] = 'best[height<=1080]/best'
        status_text = "⏳ 1080p အရည်အသွေးဖြင့် ဒေါင်းလုပ်ဆွဲနေပါပြီ..."
    elif choice == "qual_720":
        ydl_opts['format'] = 'best[height<=720]/best'
        status_text = "⏳ 720p အရည်အသွေးဖြင့် ဒေါင်းလုပ်ဆွဲနေပါပြီ..."
    elif choice == "qual_360":
        ydl_opts['format'] = 'best[height<=360]/best'
        status_text = "⏳ 360p အရည်အသွေးဖြင့် ဒေါင်းလုပ်ဆွဲနေပါပြီ..."
    elif choice == "qual_mp3":
        is_audio = True
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
        status_text = MSG_CONVERTING
    else:
        ydl_opts['format'] = 'best'
        status_text = MSG_DOWNLOADING

    status_msg = await query.edit_message_text(status_text)
    filename = None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if is_audio:
                filename = os.path.splitext(filename)[0] + ".mp3"

        await status_msg.edit_text(MSG_UPLOADING)

        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                if is_audio:
                    await query.message.reply_audio(audio=f)
                else:
                    await query.message.reply_video(video=f)
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
    TOKEN = "8419613072:AAE18KPeswX2PtMmkDrdjCw-nNoy5p7xrEs"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("🤖 Telegram Downloader Bot အောင်မြင်စွာ စတင်လည်ပတ်နေပါပြီ...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
