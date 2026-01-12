import os
import asyncio
import threading
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from telegram import Update

from queue_manager import UploadQueue
from dashboard import app, bind_queue
import uvicorn

TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

queue = UploadQueue(concurrency=3)
bind_queue(queue)


async def upload_handler(item):
    # 👇 your actual upload logic goes here
    await asyncio.sleep(1)


# ======================
# Telegram Commands
# ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send files — they will be queued and uploaded.")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📊 Bot Stats\n\n"
        f"Pending: {queue.pending()}\n"
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


async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await queue.push(update.message)
    await update.message.reply_text("📥 Added to queue")


# ======================
# Dashboard server
# ======================

def run_dashboard():
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ======================
# Main
# ======================

async def main():
    threading.Thread(target=run_dashboard, daemon=True).start()

    app = ApplicationBuilder().token(TOKEN).build()

    await queue.start(upload_handler)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("pause", pause))
    app.add_handler(CommandHandler("resume", resume))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.Video.ALL | filters.Audio.ALL, receive_file))

    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
