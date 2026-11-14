from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import database as db
from keyboards import BTN_NEWS
from services.broadcast import format_announcement
from ui import header, short_date

router = Router()


@router.message(F.text == BTN_NEWS)
async def show_news(message: Message, state: FSMContext):
    await state.clear()
    items = await db.latest_announcements(5)
    if not items:
        await message.answer(header("📢", "E'lonlar") + "\n<blockquote>Hozircha e'lonlar yo'q.</blockquote>")
        return
    await message.answer(header("📢", "So'nggi e'lonlar") + "\n<i>Eng yangilari avval</i> 👇")
    for item in items:
        text = format_announcement(item["title"], item["text"], item["url"])
        await message.answer(f"{text}\n\n<i>🗓 {short_date(item['created_at'])}</i>")
