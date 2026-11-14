import csv
import io

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

import database as db
from config import OWNER_ID
from filters import PLAIN_TEXT, IsAdmin
from keyboards import (
    admin_panel,
    admins_kb,
    confirm_kb,
    finish_quiz_kb,
    quiz_list_kb,
)
from services.broadcast import format_announcement, publish_announcement
from states import AdminEdit, AdminReply, Broadcast, NewQuiz
from ui import LINE, esc, header

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

QUESTION_HELP = (
    "✍️ <b>Savolni yuboring</b>\n\n"
    "Format (to'g'ri javob oldiga <b>+</b> qo'ying):\n\n"
    "<code>Toshkent qaysi davlat poytaxti?\n"
    "+O'zbekiston\n"
    "Qozog'iston\n"
    "Qirg'iziston</code>\n\n"
    "2 tadan 8 tagacha variant bo'lishi mumkin. Savollar tugagach «Tugatish» tugmasini bosing."
)


def parse_question(text):
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if not 3 <= len(lines) <= 9:
        return None
    options, correct = [], None
    for i, line in enumerate(lines[1:]):
        if line.startswith("+"):
            if correct is not None:
                return None
            correct = i
            line = line[1:].strip()
        options.append(line)
    if correct is None or not all(options):
        return None
    return {"text": lines[0], "options": options, "correct": correct}


async def panel_text():
    s = await db.stats()
    return (
        header("🛠", "Admin panel")
        + f"\n👥 Foydalanuvchilar: <b>{s['users']}</b>\n"
        f"📝 Quizlar: <b>{s['quizzes']}</b>\n"
        f"📢 E'lonlar: <b>{s['announcements']}</b>"
    )


@router.message(Command("admin"))
async def open_panel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        await panel_text(), reply_markup=admin_panel(message.from_user.id == OWNER_ID)
    )


@router.callback_query(F.data == "adm:back")
async def back(call: CallbackQuery):
    await call.message.edit_text(
        await panel_text(), reply_markup=admin_panel(call.from_user.id == OWNER_ID)
    )
    await call.answer()


# ---- statistika ----
@router.callback_query(F.data == "adm:stats")
async def stats(call: CallbackQuery):
    s = await db.stats()
    await call.message.answer(
        header("📊", "Statistika")
        + f"\n👥 Jami foydalanuvchilar: <b>{s['users']}</b>\n"
        f"🆕 So'nggi 24 soatda qo'shilgan: <b>{s['new_24h']}</b>\n"
        f"🔥 So'nggi 24 soatda faol: <b>{s['active_24h']}</b>\n\n"
        f"📝 Quizlar: <b>{s['quizzes']}</b>\n"
        f"🎯 Yechilgan urinishlar: <b>{s['attempts']}</b>\n"
        f"📢 E'lonlar: <b>{s['announcements']}</b>"
    )
    await call.answer()


# ---- natijalarni yuklab olish ----
@router.callback_query(F.data == "adm:export")
async def export_results(call: CallbackQuery):
    rows = await db.export_results()
    if not rows:
        await call.answer("Hozircha natijalar yo'q", show_alert=True)
        return
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Ism", "Username", "Quiz", "Ball", "Jami", "Sana (UTC)"])
    for r in rows:
        writer.writerow(
            [r["full_name"], r["username"] or "", r["title"], r["score"], r["total"], r["finished_at"]]
        )
    # utf-8-sig: Excel o'zbekcha harflarni to'g'ri ochishi uchun
    data = buffer.getvalue().encode("utf-8-sig")
    await call.message.answer_document(
        BufferedInputFile(data, filename="natijalar.csv"),
        caption=f"📥 Barcha natijalar: {len(rows)} ta yozuv",
    )
    await call.answer()


# ---- yangi quiz ----
@router.callback_query(F.data == "adm:new_quiz")
async def new_quiz(call: CallbackQuery, state: FSMContext):
    await state.set_state(NewQuiz.title)
    await call.message.answer("📝 Quiz nomini yozing:\n<i>Bekor qilish: /cancel</i>")
    await call.answer()


@router.message(NewQuiz.title, PLAIN_TEXT)
async def quiz_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip(), questions=[])
    await state.set_state(NewQuiz.questions)
    await message.answer(QUESTION_HELP)


@router.message(NewQuiz.questions, PLAIN_TEXT)
async def quiz_question(message: Message, state: FSMContext):
    question = parse_question(message.text)
    if not question:
        await message.answer("⚠️ Format noto'g'ri.\n\n" + QUESTION_HELP)
        return
    data = await state.get_data()
    questions = data["questions"] + [question]
    await state.update_data(questions=questions)
    await message.answer(
        f"✅ Savol qo'shildi (jami: <b>{len(questions)}</b>). Keyingisini yuboring yoki tugating.",
        reply_markup=finish_quiz_kb(),
    )


@router.callback_query(NewQuiz.questions, F.data == "adm:quiz_done")
async def quiz_done(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data["questions"]:
        await call.answer("Kamida bitta savol kerak", show_alert=True)
        return
    quiz_id = await db.create_quiz(data["title"], data["questions"])
    await state.clear()
    await call.message.answer(
        f"🎉 Quiz saqlandi!\n\n📝 <b>{esc(data['title'])}</b>\n"
        f"Savollar: <b>{len(data['questions'])}</b> · ID: <code>{quiz_id}</code>"
    )
    await call.answer()


# ---- quizni o'chirish ----
@router.callback_query(F.data == "adm:del_quiz")
async def del_quiz_list(call: CallbackQuery):
    quizzes = await db.list_quizzes()
    if not quizzes:
        await call.answer("Quizlar yo'q", show_alert=True)
        return
    await call.message.answer(
        "🗑 Qaysi quiz o'chirilsin?",
        reply_markup=quiz_list_kb(quizzes, prefix="delq", show_done=False),
    )
    await call.answer()


@router.callback_query(F.data.startswith("delq:"))
async def del_quiz_confirm(call: CallbackQuery):
    quiz_id = int(call.data.split(":")[1])
    quiz = await db.get_quiz(quiz_id)
    if not quiz:
        await call.answer("Quiz topilmadi", show_alert=True)
        return
    await call.message.edit_text(
        f"⚠️ <b>{esc(quiz['title'])}</b> o'chirilsinmi?\nUning barcha natijalari ham o'chadi.",
        reply_markup=confirm_kb(f"delok:{quiz_id}", "delno", yes_text="🗑 Ha, o'chirish"),
    )
    await call.answer()


@router.callback_query(F.data.startswith("delok:"))
async def del_quiz(call: CallbackQuery):
    await db.delete_quiz(int(call.data.split(":")[1]))
    await call.message.edit_text("🗑 Quiz o'chirildi.")
    await call.answer()


@router.callback_query(F.data == "delno")
async def del_quiz_cancel(call: CallbackQuery):
    await call.message.edit_text("✖️ Bekor qilindi.")
    await call.answer()


# ---- e'lon yuborish (oldindan ko'rish bilan) ----
@router.callback_query(F.data == "adm:broadcast")
async def broadcast_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(Broadcast.text)
    await call.message.answer("📢 E'lon matnini yuboring:\n<i>Bekor qilish: /cancel</i>")
    await call.answer()


@router.message(Broadcast.text, PLAIN_TEXT)
async def broadcast_preview(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await state.set_state(Broadcast.confirm)
    users = await db.count_users()
    await message.answer(
        "👁 <b>Ko'rinishi:</b>\n\n"
        + format_announcement("E'lon", message.text)
        + f"\n\n{LINE}\n<b>{users}</b> ta foydalanuvchiga yuborilsinmi?",
        reply_markup=confirm_kb("bc:yes", "bc:no", yes_text="🚀 Yuborish"),
    )


@router.callback_query(Broadcast.confirm, F.data == "bc:yes")
async def broadcast_send(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    await call.message.edit_text("⏳ Yuborilmoqda...")
    await call.answer()
    await db.add_announcement("E'lon", data["text"])
    sent, failed = await publish_announcement(call.bot, "E'lon", data["text"])
    await call.message.answer(f"✅ Yuborildi: <b>{sent}</b>\nYetib bormadi: <b>{failed}</b>")


@router.callback_query(Broadcast.confirm, F.data == "bc:no")
async def broadcast_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("✖️ E'lon bekor qilindi.")
    await call.answer()


# ---- murojaatga javob ----
@router.callback_query(F.data.startswith("reply:"))
async def reply_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminReply.text)
    await state.update_data(target=int(call.data.split(":")[1]))
    await call.message.answer("↩️ Javobingizni yozing:\n<i>Bekor qilish: /cancel</i>")
    await call.answer()


@router.message(AdminReply.text, PLAIN_TEXT)
async def reply_send(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    try:
        await message.bot.send_message(
            data["target"], f"💬 <b>Admin javobi</b>\n{LINE}\n\n{esc(message.text)}"
        )
        await message.answer("✅ Javob yuborildi.")
    except TelegramAPIError:
        await message.answer("⚠️ Javobni yetkazib bo'lmadi (foydalanuvchi botni bloklagan bo'lishi mumkin).")


# ---- adminlarni boshqarish (faqat egasi) ----
@router.callback_query(F.data == "adm:admins")
async def admins_menu(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        await call.answer("Faqat bosh admin uchun", show_alert=True)
        return
    ids = await db.list_admins()
    text = header("👤", "Adminlar") + "\n" + "\n".join(
        f"• <code>{i}</code>{' 👑' if i == OWNER_ID else ''}" for i in ids
    )
    await call.message.edit_text(text, reply_markup=admins_kb())
    await call.answer()


@router.callback_query(F.data == "adm:add_admin")
async def add_admin_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        await call.answer("Faqat bosh admin uchun", show_alert=True)
        return
    await state.set_state(AdminEdit.add_admin)
    await call.message.answer("Yangi adminning Telegram ID sini yuboring:\n<i>Bekor qilish: /cancel</i>")
    await call.answer()


@router.message(AdminEdit.add_admin, PLAIN_TEXT)
async def add_admin_save(message: Message, state: FSMContext):
    if message.from_user.id != OWNER_ID:
        return
    if not message.text.strip().isdigit():
        await message.answer("ID faqat raqamlardan iborat bo'lishi kerak.")
        return
    await db.add_admin(int(message.text.strip()))
    await state.clear()
    await message.answer("✅ Admin qo'shildi.")


@router.callback_query(F.data == "adm:rm_admin")
async def rm_admin_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        await call.answer("Faqat bosh admin uchun", show_alert=True)
        return
    await state.set_state(AdminEdit.remove_admin)
    await call.message.answer("O'chiriladigan adminning ID sini yuboring:\n<i>Bekor qilish: /cancel</i>")
    await call.answer()


@router.message(AdminEdit.remove_admin, PLAIN_TEXT)
async def rm_admin_save(message: Message, state: FSMContext):
    if message.from_user.id != OWNER_ID:
        return
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("ID faqat raqamlardan iborat bo'lishi kerak.")
        return
    if int(text) == OWNER_ID:
        await message.answer("Bosh adminni o'chirib bo'lmaydi.")
        return
    await db.remove_admin(int(text))
    await state.clear()
    await message.answer("✅ Admin o'chirildi.")
