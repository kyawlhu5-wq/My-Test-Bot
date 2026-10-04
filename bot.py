import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp

# Logging သတ်မှတ်ချက်
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==================== ✍️ စာသားများကို ဤနေရာတွင် ပြင်ဆင်နိုင်ပါသည် ====================
MSG_START_WELCOME = "👋 မင်္ဂလာပါဆရာ။ 🔗 ဒေါင်းလုပ်ဆွဲလိုတဲ့ YouTube, Facebook, TikTok နဲ့ အခြားလင့်ခ်တစ်ခုခုကို ပို့ပေးပါခင်ဗျာ。"
MSG_INVALID_URL   = "⚠️ တောင်းပန်ပါတယ်ဆရာ၊ ပို့လိုက်တဲ့ စာသားမှာ မှန်ကန်တဲ့ လင့်ခ် (URL) မတွေ့ရလို့ပါ။ ကျေးဇူးပြု၍ လင့်ခ်မှန်မှန်ကန်ကန် ပို့ပေးပါ။"
MSG_CHOICE_PROMPT = "📥 လင့်ခ်ကို စစ်ဆေးတွေ့ရှိပါပြီ။ ဘယ်လို ပုံစံနဲ့ ဒေါင်းလုပ်ဆွဲချင်ပါသလဲဆရာ?"
MSG_DOWNLOADING   = "⏳ ခဏစောင့်ပါဆရာ၊ ဖိုင်ကို ဆာဗာပေါ်သို့ ဒေါင်းလုပ်ဆွဲနေပါပြီ... (Short/Reels ဆိုရင် ခဏလေးပဲ ကြာပါမယ်)"
MSG_CONVERTING    = "🔄 အသံဖိုင် (MP3) သို့ ပြောင်းလဲနေပါပြီဆရာ၊ ကျေးဇူးပြု၍ ခဏစောင့်ပေးပါ။"
MSG_UPLOADING     = "📤 ဖိုင်ဒေါင်းလို့ပြီးပါပြီ။ Telegram ဆာဗာဆီသို့ ပို့ဆောင်နေပါပြီခင်ဗျာ..."
MSG_ERROR         = "❌ ဒေါင်းလုပ်ဆွဲရာတွင် အမှားအယွင်း ရှိသွားပါသည်ဆရာ (လင့်ခ်သေနေခြင်း သို့မဟုတ် ဖိုင်ကြီးလွန်းခြင်း ဖြစ်နိုင်ပါသည်): {error}"
# ====================================================================================

# 1. /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(MSG_START_WELCOME)

# 2. Handle Text Link Message
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    if not url.startswith("http"):
        await update.message.reply_text(MSG_INVALID_URL)
        return

    # URL ကို context ထဲမှာ ယာယီသိမ်းထားခြင်း
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

# 3. Handle Button Clicks (Video or MP3)
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    url = context.user_data.get('target_url')
    if not url:
        await query.edit_message_text("❌ လင့်ခ် သက်တမ်းကုန်သွားပါပြီ။ ကျေးဇူးပြု၍ လင့်ခ်အသစ် ပြန်ပို့ပေးပါ။")
        return

    download_type = query.data # 'type_video' သို့မဟုတ် 'type_audio'
    os.makedirs('downloads', exist_ok=True)

    if download_type == "type_video":
        status_msg = await query.edit_message_text(MSG_DOWNLOADING)
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
        }
    else:
        status_msg = await query.edit_message_text(MSG_CONVERTING)
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if download_type == "type_audio":
                # MP3 ပြောင်းသွားပါက extension ကို .mp3 သို့ ပြောင်းရန်
                filename = os.path.splitext(filename)[0] + ".mp3"

        await status_msg.edit_text(MSG_UPLOADING)

        # Telegram သို့ ဖိုင်ပြန်လည် ပို့ဆောင်ခြင်း
        with open(filename, 'rb') as f:
            if download_type == "type_video":
                await query.message.reply_video(video=f)
            else:
                await query.message.reply_audio(audio=f)

        # Server Clean up (ဖိုင်ဖျက်ခြင်း)
        if os.path.exists(filename):
            os.remove(filename)
            
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(MSG_ERROR.format(error=str(e)))

def main():
    # Bot Token ကို အသင့်ထည့်သွင်းပေးထားပါပြီ
    TOKEN = "8419613072:AAHy1x_3eJOvjp5l-gAgMiJTtkrS5X84niA"
    
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers များ
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("🤖 Multi-Platform Download Bot အောင်မြင်စွာ စတင်လည်ပတ်နေပါပြီ...")
    app.run_polling()

if __name__ == '__main__':
    main()
