import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from config import CHANNEL_LINK, REQUIRED_CHANNEL


async def is_subscribed(bot: Bot, user_id: int) -> bool:
    """Majburiy kanalga obunani tekshiradi. Tekshirib bo'lmasa (masalan, bot kanalda admin emas),
    foydalanuvchini to'smaydi."""
    if not REQUIRED_CHANNEL:
        return True
    try:
        member = await bot.get_chat_member(REQUIRED_CHANNEL, user_id)
    except TelegramAPIError:
        logging.warning("Obunani tekshirib bo'lmadi: botni kanalga admin qiling (%s)", REQUIRED_CHANNEL)
        return True
    if member.status in ("creator", "administrator", "member"):
        return True
    if member.status == "restricted":
        return bool(getattr(member, "is_member", False))
    return False


def channel_url():
    if CHANNEL_LINK:
        return CHANNEL_LINK
    if REQUIRED_CHANNEL.startswith("@"):
        return f"https://t.me/{REQUIRED_CHANNEL[1:]}"
    return None
