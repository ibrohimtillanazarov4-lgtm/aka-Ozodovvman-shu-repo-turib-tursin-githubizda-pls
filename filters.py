from aiogram import F
from aiogram.filters import BaseFilter

import database as db
from keyboards import MENU_TEXTS


class IsAdmin(BaseFilter):
    async def __call__(self, event) -> bool:
        return await db.is_admin(event.from_user.id)


# Oddiy matn: buyruq ham, menyu tugmasi ham emas (holatlarda matn qabul qilish uchun)
PLAIN_TEXT = F.text & ~F.text.startswith("/") & ~F.text.in_(MENU_TEXTS)
