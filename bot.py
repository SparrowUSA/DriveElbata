import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from drive_upload import upload_file_bytes


TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me ANY file (photo/video/document/audio) and I will upload it to Google Drive without using your storage.\n\nSupports bulk later (1–1000)."
    )


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_obj = None
    file_name = "file"

    # Documents
    if update.message.document:
        file_obj = update.message.document.get_file()
        file_name = update.message.document.file_name

    # Videos
    elif update.message.video:
        file_obj = update.message.video.get_file()
        file_name = "video.mp4"

    # Photos
    elif update.message.photo:
        file_obj = await update.message.photo[-1].get_file()
        file_name = "photo.jpg"

    # Audio
    elif update.message.audio:
        file_obj = update.message.audio.get_file()
        file_name = update.message.audio.file_name

    else:
        await update.message.reply_text("Please send a file, photo, video, or document.")
        return

    # Download file into RAM (NOT LOCAL DISK)
    file_bytes = await file_obj.download_as_bytearray()

    uploaded = upload_file_bytes(file_name, bytes(file_bytes))

    await update.message.reply_text(
        f"Uploaded successfully!\n\nDrive link:\n{uploaded['webViewLink']}"
    )


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_file))

    app.run_polling()


if __name__ == "__main__":
    main()
