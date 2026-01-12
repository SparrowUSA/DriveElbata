from telegram import Message
from telegram.ext import ContextTypes


async def fetch_single_file(message: Message):
    """
    Extracts a single Telegram file object + filename
    Works for: photo, video, document, audio
    """

    if message.document:
        file = await message.document.get_file()
        filename = message.document.file_name or "document.bin"

    elif message.video:
        file = await message.video.get_file()
        filename = message.video.file_name or "video.mp4"

    elif message.photo:
        file = await message.photo[-1].get_file()
        filename = "photo.jpg"

    elif message.audio:
        file = await message.audio.get_file()
        filename = message.audio.file_name or "audio.mp3"

    else:
        return None

    return file, filename



async def fetch_from_channel(context: ContextTypes.DEFAULT_TYPE, channel_id: int, limit: int = 100):
    """
    Fetch last N media messages from a channel.
    Works for private channels if bot is a member.
    """

    result = []

    async for msg in context.bot.get_chat_history(chat_id=channel_id, limit=limit):

        data = await fetch_single_file(msg)

        if data:
            result.append(data)

    return result

