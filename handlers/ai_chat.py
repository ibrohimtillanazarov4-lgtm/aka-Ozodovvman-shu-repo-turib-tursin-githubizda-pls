from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards import BTN_AI, BTN_EXIT_AI, ai_menu, main_menu
from services import ai
from states import AiChat
from ui import ai_to_html, header

router = Router()

MAX_HISTORY = 10


@router.message(F.text == BTN_AI)
async def enter_ai(message: Message, state: FSMContext):
    await state.set_state(AiChat.active)
    await state.update_data(history=[])
    await message.answer(
        header("🤖", "AI yordamchi")
        + "\nSavolingizni yozing — darslar, uy vazifasi yoki dasturlash bo'yicha yordam beraman.\n\n"
        "<i>Chiqish uchun pastdagi tugmani bosing.</i>",
        reply_markup=ai_menu(),
    )


@router.message(AiChat.active, F.text == BTN_EXIT_AI)
async def exit_ai(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyuga qaytdingiz 🏠", reply_markup=main_menu())


@router.message(AiChat.active, F.text)
async def chat(message: Message, state: FSMContext):
    data = await state.get_data()
    history = data.get("history", [])
    history.append({"role": "user", "content": message.text})

    await message.bot.send_chat_action(message.chat.id, "typing")
    reply = await ai.ask(history[-MAX_HISTORY:])

    history.append({"role": "assistant", "content": reply})
    await state.update_data(history=history[-MAX_HISTORY:])
    await message.answer(ai_to_html(reply))
