import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramNetworkError
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, ErrorEvent
from aiohttp import web

import database as db
from config import BOT_TOKEN, PORT, SITE_API_KEY
from handlers import admin, ai_chat, announcements, quiz, user
from ui import BOT_NAME
from middlewares import SubscriptionMiddleware, ThrottleMiddleware
from services.api import create_app

COMMANDS = [
    BotCommand(command="start", description="Bosh menyu"),
    BotCommand(command="quizlar", description="Quizlar ro'yxati"),
    BotCommand(command="reyting", description="Eng yaxshi o'quvchilar"),
    BotCommand(command="profil", description="Mening natijalarim"),
    BotCommand(command="help", description="Bot haqida"),
    BotCommand(command="cancel", description="Joriy amalni bekor qilish"),
]


async def on_error(event: ErrorEvent):
    logging.exception("Kutilmagan xatolik", exc_info=event.exception)
    update = event.update
    target = update.message or (update.callback_query.message if update.callback_query else None)
    if target:
        try:
            await target.answer("⚠️ Kutilmagan xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
        except Exception:
            pass
    return True


async def retry_network(func, *args, attempts=6, **kwargs):
    """Telegram bilan vaqtincha aloqa uzilsa (timeout), bir necha marta qayta urinadi."""
    for i in range(1, attempts + 1):
        try:
            return await func(*args, **kwargs)
        except TelegramNetworkError as e:
            if i == attempts:
                raise
            delay = min(2 * i, 15)
            logging.warning("Telegram tarmoq xatosi (%s). %s soniyadan keyin qayta uriniladi (%s/%s)", e, delay, i, attempts)
            await asyncio.sleep(delay)


async def setup_profile(bot: Bot):
    """Bot menyusi va tavsifini o'rnatadi (xato bo'lsa, ishga tushishga xalaqit bermaydi)."""
    try:
        await retry_network(bot.set_my_commands, COMMANDS)
        await retry_network(bot.set_my_short_description, f"{BOT_NAME} — IT o'rganuvchilar uchun quiz, e'lon va AI yordamchi")
        await retry_network(bot.set_my_description,
            f"💻 {BOT_NAME} · IT ta'lim boti\n\n"
            "📝 Quizlar va reyting\n📢 Musobaqa e'lonlari\n🤖 AI yordamchi\n✉️ Adminga murojaat\n\n"
            "Boshlash uchun START tugmasini bosing."
        )
    except Exception:
        logging.warning("Bot profilini o'rnatib bo'lmadi", exc_info=True)


async def main():
    logging.basicConfig(level=logging.INFO)
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN topilmadi. .env faylini tekshiring.")

    await db.init_db()

    session = AiohttpSession(timeout=90)  # standart 60 soniya, sekin tarmoqda yetmasligi mumkin
    bot = Bot(BOT_TOKEN, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # himoya qatlamlari: avval spam filtri, keyin majburiy obuna
    for observer in (dp.message, dp.callback_query):
        observer.outer_middleware(ThrottleMiddleware())
        observer.outer_middleware(SubscriptionMiddleware())
    dp.errors.register(on_error)

    # tartib muhim: admin va menyu tugmalari AI rejimidan oldin tekshiriladi
    dp.include_routers(
        admin.router, user.router, quiz.router, announcements.router, ai_chat.router
    )

    # sayt bilan aloqa uchun veb-server (bot bilan bir jarayonda ishlaydi)
    runner = web.AppRunner(create_app(bot, SITE_API_KEY))
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()

    try:
        await retry_network(bot.delete_webhook, drop_pending_updates=True)
        await setup_profile(bot)
        await dp.start_polling(bot, polling_timeout=30)
    finally:
        await runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
