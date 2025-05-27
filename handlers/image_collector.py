from aiogram.types import Message
from aiogram import Router

from config import GARBAGE_CHAT_ID
from filters.filter import ChatFilter
from main import photo_cache

router = Router()

@router.message(ChatFilter(chat_id=GARBAGE_CHAT_ID))
async def handle_channel_photo(message: Message):
    if not message.photo or not message.caption:
        return

    largest_photo = message.photo[-1]
    photo_id = largest_photo.file_id
    caption = message.caption.strip()

    photo_cache[caption] = photo_id
    print(f"{caption} -> {photo_id}")
