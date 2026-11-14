import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter

import database as db
from config import ANNOUNCE_CHANNEL
from ui import LINE, esc, esc_attr


def format_announcement(title, text, url=None):
    message = f"📢 <b>{esc(title)}</b>\n{LINE}\n\n{esc(text)}"
    if url:
        message += f'\n\n🔗 <a href="{esc_attr(url)}">Batafsil</a>'
    return message


async def _send(bot: Bot, user_id, text):
    try:
        await bot.send_message(user_id, text)
        return True
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after)
        return await _send(bot, user_id, text)
    except TelegramAPIError:
        return False


async def send_to_all(bot: Bot, text: str):
    sent = failed = 0
    for user_id in await db.all_user_ids():
        if await _send(bot, user_id, text):
            sent += 1
        else:
            failed += 1
        await asyncio.sleep(0.05)  # Telegram limitlariga tushmaslik uchun
    return sent, failed


async def publish_announcement(bot: Bot, title, text, url=None):
    """E'lonni (sozlangan bo'lsa) kanalga va barcha foydalanuvchilarga yuboradi."""
    message = format_announcement(title, text, url)
    if ANNOUNCE_CHANNEL:
        try:
            await bot.send_message(ANNOUNCE_CHANNEL, message)
        except TelegramAPIError:
            logging.warning("E'lonni kanalga joylab bo'lmadi (%s)", ANNOUNCE_CHANNEL)
    return await send_to_all(bot, message)
