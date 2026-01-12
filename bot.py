import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from drive_upload import upload_file_bytes
from queue_manager import UploadQueue


TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

queue = UploadQueue(concurrency=3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ Cloud Bulk Google Drive Bot\n\n"
        "Commands:\n"
        "/upload_channel <channel> <count>\n"
        "— Upload 1–1000 recent files from channel\n\n"
        "Send any file to upload individually."
    )


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_obj = None
    file_name = "file"

    if update.message.document:
        file_obj = await update.message.document.get_file()
        file_name = update.message.document.file_name

    elif update.message.video:
        file_obj = await update.message.video.get_file()
        file_name = "video.mp4"

    elif update.message.photo:
        file_obj = await update.message.photo[-1].get_file()
        file_name = "photo.jpg"

    else:
        await update.message.reply_text("Send a file/video/photo.")
        return

    file_bytes = await file_obj.download_as_bytearray()

    uploaded = upload_file_bytes(file_name, bytes(file_bytes))

    await update.message.reply_text(f"Uploaded:\n{uploaded['webViewLink']}")


# ---------------- BULK UPLOAD -----------------

async def upload_single_message(msg, chat, update):
    try:
        file = await msg.get_file()

        if msg.video:
            name = f"{chat}_video_{msg.id}.mp4"
        elif msg.photo:
            name = f"{chat}_photo_{msg.id}.jpg"
        elif msg.document:
            name = msg.document.file_name or f"{chat}_document_{msg.id}"
        else:
            return

        file_bytes = await file.download_as_bytearray()

        uploaded = upload_file_bytes(name, bytes(file_bytes))

        await update.message.reply_text(f"Uploaded: {name}")
    except Exception as e:
        await update.message.reply_text(f"Retrying {msg.id}…")
        await upload_single_message(msg, chat, update)


async def upload_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage:\n/upload_channel <channel> <1-1000>")
        return

    channel = context.args[0]
    limit = int(context.args[1])

    if limit < 1 or limit > 1000:
        await update.message.reply_text("Limit must be 1–1000")
        return

    chat = await context.bot.get_chat(channel)

    messages = []
    async for msg in context.bot.get_chat_history(chat.id, limit=limit):
        messages.append(msg)

    messages = list(reversed(messages))

    await update.message.reply_text(f"Found {len(messages)} messages. Starting upload…")

    async def handler(item):
        await upload_single_message(item, channel, update)

    await queue.start(handler)

    for m in messages:
        await queue.push(m)


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("upload_channel", upload_channel))
    app.add_handler(MessageHandler(filters.ALL, handle_file))

    app.run_polling()


if __name__ == "__main__":
    main()
