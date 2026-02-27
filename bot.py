import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Secure token from environment
BOT_TOKEN = os.getenv("8617066051:AAGzYL_z4G5h_8vLPrKHsQzVQrpEE3fLXIQ")

DOWNLOAD_PATH = "downloads"
COOKIE_FILE = "cookies.txt"

os.makedirs(DOWNLOAD_PATH, exist_ok=True)

user_links = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Send YouTube link\nThen select Video or Audio."
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user_links[update.message.chat_id] = url

    keyboard = [
        [
            InlineKeyboardButton("🎥 Video", callback_data="video"),
            InlineKeyboardButton("🎵 Audio (MP3)", callback_data="audio"),
        ]
    ]

    await update.message.reply_text(
        "Select format:", reply_markup=InlineKeyboardMarkup(keyboard)
    )

def get_ydl_opts(format_string):
    return {
        "format": format_string,
        "outtmpl": f"{DOWNLOAD_PATH}/%(title).80s.%(ext)s",
        "merge_output_format": "mp4",
        "quiet": True,
        "cookiefile": COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
        "noplaylist": True,
    }

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    url = user_links.get(chat_id)

    if not url:
        await query.edit_message_text("❌ Link expired. Send again.")
        return

    if query.data == "video":
        keyboard = [
            [
                InlineKeyboardButton("360p", callback_data="360"),
                InlineKeyboardButton("720p", callback_data="720"),
                InlineKeyboardButton("1080p", callback_data="1080"),
            ]
        ]
        await query.edit_message_text(
            "Choose quality:", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if query.data == "audio":
        await query.edit_message_text("🎵 Downloading MP3...")

        ydl_opts = get_ydl_opts("bestaudio")

        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]

    else:
        quality = query.data
        await query.edit_message_text(f"🎥 Downloading {quality}p...")
        ydl_opts = get_ydl_opts(
            f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]"
        )

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if query.data == "audio":
            filename = filename.rsplit(".", 1)[0] + ".mp3"
            await context.bot.send_audio(chat_id=chat_id, audio=open(filename, "rb"))
        else:
            if not filename.endswith(".mp4"):
                filename = filename.rsplit(".", 1)[0] + ".mp4"

            file_size = os.path.getsize(filename)

            if file_size > 50 * 1024 * 1024:
                await context.bot.send_document(chat_id=chat_id, document=open(filename, "rb"))
            else:
                await context.bot.send_video(chat_id=chat_id, video=open(filename, "rb"))

        os.remove(filename)

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Error: {e}")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()
