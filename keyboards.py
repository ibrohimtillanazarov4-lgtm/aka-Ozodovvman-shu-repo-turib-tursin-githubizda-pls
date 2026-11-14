from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

BTN_QUIZ = "📝 Quizlar"
BTN_TOP = "🏆 Reyting"
BTN_NEWS = "📢 E'lonlar"
BTN_PROFILE = "👤 Profil"
BTN_AI = "🤖 AI yordamchi"
BTN_CONTACT = "✉️ Murojaat"
BTN_ABOUT = "ℹ️ Bot haqida"
BTN_EXIT_AI = "⬅️ Chiqish"

MENU_TEXTS = frozenset(
    {BTN_QUIZ, BTN_TOP, BTN_NEWS, BTN_PROFILE, BTN_AI, BTN_CONTACT, BTN_ABOUT, BTN_EXIT_AI}
)

LETTERS = "ABCDEFGH"
CIRCLED = "ⒶⒷⒸⒹⒺⒻⒼⒽ"


def _btn(text, data):
    return InlineKeyboardButton(text=text, callback_data=data)


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_QUIZ), KeyboardButton(text=BTN_TOP)],
            [KeyboardButton(text=BTN_NEWS), KeyboardButton(text=BTN_PROFILE)],
            [KeyboardButton(text=BTN_AI), KeyboardButton(text=BTN_CONTACT)],
            [KeyboardButton(text=BTN_ABOUT)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Bo'limni tanlang 👇",
    )


def ai_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_EXIT_AI)]],
        resize_keyboard=True,
        input_field_placeholder="Savolingizni yozing...",
    )


def quiz_list_kb(quizzes, prefix="quiz", show_done=True):
    rows = []
    for q in quizzes:
        icon = "✅" if show_done and q["done"] else "🔹"
        rows.append([_btn(f"{icon}  {q['title']}  ·  {q['n']} savol", f"{prefix}:{q['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def options_kb(idx, count):
    letters = [_btn(CIRCLED[i], f"ans:{idx}:{i}") for i in range(count)]
    rows = [letters[i : i + 4] for i in range(0, len(letters), 4)]
    rows.append([_btn("✕  To'xtatish", "quiz_stop")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def result_kb(quiz_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn("🔁 Qayta urinish", f"quiz:{quiz_id}"), _btn("📝 Quizlar", "go:quiz")]
        ]
    )


def subscribe_kb(url):
    rows = []
    if url:
        rows.append([InlineKeyboardButton(text="📣 Kanalga o'tish", url=url)])
    rows.append([_btn("✅ Obuna bo'ldim", "check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_kb(yes_data, no_data, yes_text="✅ Ha", no_text="✖️ Bekor qilish"):
    return InlineKeyboardMarkup(inline_keyboard=[[_btn(yes_text, yes_data), _btn(no_text, no_data)]])


def reply_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[[_btn("↩️ Javob berish", f"reply:{user_id}")]])


def admin_panel(is_owner):
    rows = [
        [_btn("➕ Yangi quiz", "adm:new_quiz"), _btn("🗑 Quizni o'chirish", "adm:del_quiz")],
        [_btn("📢 E'lon yuborish", "adm:broadcast"), _btn("📊 Statistika", "adm:stats")],
        [_btn("📥 Natijalar (CSV)", "adm:export")],
    ]
    if is_owner:
        rows.append([_btn("👤 Adminlar", "adm:admins")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admins_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn("➕ Admin qo'shish", "adm:add_admin"), _btn("➖ Admin o'chirish", "adm:rm_admin")],
            [_btn("⬅️ Orqaga", "adm:back")],
        ]
    )


def finish_quiz_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[_btn("✅ Tugatish", "adm:quiz_done")]])
