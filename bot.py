import os
import asyncio
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from queue_manager import UploadQueue
from telegram_fetch import fetch_single_file, fetch_from_channel
from drive_upload import upload_to_drive
from dashboard import app, bind_queue
import uvicorn

TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

queue = UploadQueue(concurrency=3)
bind_queue(queue)


# ------------------ Telegram Handlers ------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send any file, or use /bulk <channel_id> <count> to bulk upload 1–1000 files."
    )


async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await queue.push(update.message)
    await update.message.reply_text("📥 Added to queue")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📊 Pending: {queue.pending()}\n"
        f"Uploaded: {queue.total_uploaded}\n"
        f"Failed: {queue.total_failed}\n"
        f"Paused: {queue.paused}"
    )


async def pause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    queue.pause()
    await update.message.reply_text("⏸ Queue paused")


async def resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    queue.resume()
    await update.message.reply_text("▶ Queue resumed")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await queue.clear()
    await update.message.reply_text("🛑 Queue cleared")


# ------------------ Upload Worker ------------------

async def upload_handler(item):
    # item can be Message (single) or tuple from bulk
    if isinstance(item, tuple):
        message, (file_obj, filename) = item
    else:
        message = item
        result = await fetch_single_file(message)
        if not result:
            await message.reply_text("⚠️ Unsupported file type, skipping.")
            return
        file_obj, filename = result

    file_bytes = await file_obj.download_as_bytearray()
    drive_link = upload_to_drive(file_bytes, filename)

    if drive_link:
        await message.reply_text(f"✅ Uploaded: {filename}\n🔗 {drive_link}")
    else:
        await message.reply_text(f"❌ Upload failed: {filename}")


# ------------------ Bulk Command ------------------

async def bulk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /bulk <channel_id> <count>")
        return

    try:
        channel_id = int(context.args[0])
        limit = int(context.args[1])
        if limit < 1 or limit > 1000:
            await update.message.reply_text("Limit must be 1–1000")
            return
    except ValueError:
        await update.message.reply_text("Channel ID and count must be numbers")
        return

    await update.message.reply_text(f"Fetching last {limit} files from channel {channel_id}…")

    media_items = await fetch_from_channel(context, channel_id, limit)

    for msg, data in media_items:
        await queue.push((msg, data))

    await update.message.reply_text(f"✅ Added {len(media_items)} files to the queue")


# ------------------ Dashboard ------------------

def run_dashboard():
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ------------------ Main ------------------

async def main():
    threading.Thread(target=run_dashboard, daemon=True).start()

    app_bot = ApplicationBuilder().token(TOKEN).build()

    await queue.start(upload_handler)

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("stats", stats))
    app_bot.add_handler(CommandHandler("pause", pause))
    app_bot.add_handler(CommandHandler("resume", resume))
    app_bot.add_handler(CommandHandler("cancel", cancel))
    app_bot.add_handler(CommandHandler("bulk", bulk))
    app_bot.add_handler(
        MessageHandler(filters.Document.ALL | filters.Video.ALL | filters.Photo.ALL | filters.Audio.ALL, receive_file)
    )

    await app_bot.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
