from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database as db
from filters import PLAIN_TEXT
from keyboards import (
    BTN_ABOUT,
    BTN_CONTACT,
    BTN_PROFILE,
    BTN_TOP,
    main_menu,
    reply_kb,
)
from services.subscription import is_subscribed
from states import Contact
from ui import (
    DOT,
    LINE,
    THIN,
    about_text,
    esc,
    header,
    medal,
    mention,
    short_date,
    user_tag,
    welcome_text,
)

router = Router()


async def send_welcome(message: Message, user):
    is_new = await db.upsert_user(user.id, user.full_name, user.username)
    is_admin = await db.is_admin(user.id)
    await message.answer(welcome_text(user, is_new, is_admin), reply_markup=main_menu())


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await send_welcome(message, message.from_user)


@router.callback_query(F.data == "check_sub")
async def check_subscription(call: CallbackQuery):
    if not await is_subscribed(call.bot, call.from_user.id):
        await call.answer("Hali obuna bo'lmadingiz 🙂", show_alert=True)
        return
    await call.answer("Rahmat! ✅")
    await call.message.delete()
    await send_welcome(call.message, call.from_user)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    had_state = await state.get_state() is not None
    await state.clear()
    await message.answer(
        "✖️ Bekor qilindi." if had_state else "Bekor qilinadigan amal yo'q.",
        reply_markup=main_menu(),
    )


@router.message(Command("help"))
@router.message(F.text == BTN_ABOUT)
async def about(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(about_text())


@router.callback_query(F.data == "go:about")
async def about_cb(call: CallbackQuery):
    await call.message.answer(about_text())
    await call.answer()


# ---- reyting ----
@router.message(Command("reyting"))
@router.message(F.text == BTN_TOP)
async def show_top(message: Message, state: FSMContext):
    await state.clear()
    rows = await db.top_results()
    if not rows:
        await message.answer(
            header("🏆", "Reyting") + "\n<blockquote>Hozircha natijalar yo'q.\nBirinchi bo'ling — quiz yeching! 🚀</blockquote>"
        )
        return
    lines = []
    for i, r in enumerate(rows):
        lines.append(f"{medal(i)}  <b>{esc(r['name'])}</b>\n      <b>{r['points']}</b> ball  <i>· {r['quizzes']} quiz</i>")
        if i == 2 and len(rows) > 3:
            lines.append(THIN)
    text = header("🏆", "Eng yaxshi o'quvchilar") + "\n" + "\n".join(lines)

    mine = await db.user_progress(message.from_user.id)
    if mine:
        text += f"\n\n{LINE}\n🎯 <b>Sizning o'rningiz:</b> {mine['place']} / {mine['n']}  <i>({mine['points']} ball)</i>"
    else:
        text += f"\n\n{LINE}\n💡 <i>Siz hali quiz yechmagansiz — reytingga kirish uchun boshlang!</i>"
    await message.answer(text)


# ---- profil ----
@router.message(Command("profil"))
@router.message(F.text == BTN_PROFILE)
async def show_profile(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    await db.upsert_user(user.id, user.full_name, user.username)
    info = await db.get_user(user.id)
    progress = await db.user_progress(user.id)

    lines = [
        header("👤", "Mening profilim"),
        "<blockquote>"
        f"🙋 <b>{esc(user.full_name)}</b>\n"
        f"🔗 {user_tag(user)}\n"
        f"🆔 <code>{user.id}</code>\n"
        f"📅 <i>A'zo bo'lgan sana:</i> {short_date(info['joined_at'])}"
        "</blockquote>",
        f"\n📊 <b>Natijalar</b>\n{THIN}",
    ]
    if progress:
        lines += [
            f"{DOT} Yechilgan quizlar:  <b>{progress['quizzes']}</b>",
            f"{DOT} Jami ball:  <b>{progress['points']}</b>",
            f"{DOT} Reytingdagi o'rin:  <b>{progress['place']}</b> / {progress['n']}",
        ]
    else:
        lines.append("📭 <i>Hali quiz yechmagansiz. «📝 Quizlar» bo'limidan boshlang!</i>")
    await message.answer("\n".join(lines))


# ---- murojaat ----
@router.message(F.text == BTN_CONTACT)
async def contact_start(message: Message, state: FSMContext):
    await state.set_state(Contact.message)
    await message.answer(
        header("✉️", "Murojaat")
        + "\n<blockquote>Savol, taklif yoki shikoyatingizni yozing — adminlarga yetkazaman.</blockquote>\n"
        "<i>Bekor qilish: /cancel</i>"
    )


@router.message(Contact.message, PLAIN_TEXT)
async def contact_send(message: Message, state: FSMContext):
    user = message.from_user
    await db.upsert_user(user.id, user.full_name, user.username)
    text = (
        f"✉️  <b>YANGI MUROJAAT</b>\n{LINE}\n\n"
        f"👤 {mention(user.id, user.full_name)}  ·  <code>{user.id}</code>\n\n"
        f"<blockquote>{esc(message.text)}</blockquote>"
    )
    delivered = 0
    for admin_id in await db.list_admins():
        try:
            await message.bot.send_message(admin_id, text, reply_markup=reply_kb(user.id))
            delivered += 1
        except TelegramAPIError:
            continue
    await state.clear()
    if delivered:
        await message.answer("✅ <b>Murojaatingiz yuborildi.</b>\n<i>Tez orada javob olasiz.</i>", reply_markup=main_menu())
    else:
        await message.answer("⚠️ Hozir adminlarga yetkazib bo'lmadi. Keyinroq urinib ko'ring.", reply_markup=main_menu())


@router.message(Contact.message, ~F.text)
async def contact_non_text(message: Message):
    await message.answer("Iltimos, murojaatni matn ko'rinishida yozing yoki /cancel bosing.")
