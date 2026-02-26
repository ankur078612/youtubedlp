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

BOT_TOKEN = "8617066051:AAGzYL_z4G5h_8vLPrKHsQzVQrpEE3fLXIQ"

DOWNLOAD_PATH = "downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# Store user links temporarily
user_links = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Send me a YouTube link.\nThen choose format (Video/Audio)."
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    user_links[update.message.chat_id] = url

    keyboard = [
        [
            InlineKeyboardButton("🎥 Video", callback_data="video"),
            InlineKeyboardButton("🎵 Audio (MP3)", callback_data="audio"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select format:", reply_markup=reply_markup)

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

    elif query.data == "audio":
        await query.edit_message_text("🎵 Downloading MP3...")

        ydl_opts = {
            "format": "bestaudio",
            "outtmpl": f"{DOWNLOAD_PATH}/%(title)s.%(ext)s",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "quiet": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                filename = filename.rsplit(".", 1)[0] + ".mp3"

            await context.bot.send_audio(chat_id=chat_id, audio=open(filename, "rb"))
            os.remove(filename)

        except Exception as e:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Error: {e}")

    elif query.data in ["360", "720", "1080"]:
        quality = query.data
        await query.edit_message_text(f"🎥 Downloading {quality}p...")

        ydl_opts = {
            "format": f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]",
            "outtmpl": f"{DOWNLOAD_PATH}/%(title)s.%(ext)s",
            "merge_output_format": "mp4",
            "quiet": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if not filename.endswith(".mp4"):
                    filename = filename.rsplit(".", 1)[0] + ".mp4"

            await context.bot.send_video(chat_id=chat_id, video=open(filename, "rb"))
            os.remove(filename)

        except Exception as e:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Error: {e}")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()