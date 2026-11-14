import time

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

import database as db
from config import REQUIRED_CHANNEL
from keyboards import subscribe_kb
from services.subscription import channel_url, is_subscribed
from ui import LINE


class ThrottleMiddleware(BaseMiddleware):
    """Juda tez-tez yuborilgan xabarlarni (spam) o'tkazmaydi va faollikni yozib boradi."""

    def __init__(self, interval=0.6):
        self.interval = interval
        self.last = {}

    async def __call__(self, handler, event, data):
        user = event.from_user
        if user:
            now = time.monotonic()
            if now - self.last.get(user.id, 0) < self.interval:
                if isinstance(event, CallbackQuery):
                    await event.answer()
                return None
            self.last[user.id] = now
            if len(self.last) > 10000:
                self.last.clear()
            await db.touch_user(user.id)
        return await handler(event, data)


class SubscriptionMiddleware(BaseMiddleware):
    """REQUIRED_CHANNEL sozlangan bo'lsa, obuna bo'lmaganlarni to'xtatadi."""

    async def __call__(self, handler, event, data):
        user = event.from_user
        if not REQUIRED_CHANNEL or user is None:
            return await handler(event, data)
        if isinstance(event, CallbackQuery) and event.data == "check_sub":
            return await handler(event, data)
        if await db.is_admin(user.id) or await is_subscribed(data["bot"], user.id):
            return await handler(event, data)

        text = (
            f"📣 <b>Kanalga obuna bo'ling</b>\n{LINE}\n\n"
            "Botdan foydalanish uchun avval rasmiy kanalimizga obuna bo'ling, "
            "so'ng «✅ Obuna bo'ldim» tugmasini bosing."
        )
        target = event.message if isinstance(event, CallbackQuery) else event
        await target.answer(text, reply_markup=subscribe_kb(channel_url()))
        if isinstance(event, CallbackQuery):
            await event.answer()
        return None
