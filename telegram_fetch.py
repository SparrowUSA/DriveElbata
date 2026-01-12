from telegram import InputMediaDocument, InputMediaVideo, InputMediaPhoto

async def get_messages_from_channel(client, chat_id, limit):
    messages = []
    async for msg in client.get_chat_history(chat_id, limit=limit):
        if msg.video or msg.document or msg.photo:
            messages.append(msg)
    return list(reversed(messages))
