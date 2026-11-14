"""Matn va ko'rinish yordamchilari (HTML formatlash)."""
import html
import re
from datetime import datetime, timedelta, timezone

from config import TZ_OFFSET_HOURS

LINE = "━━━━━━━━━━━━━━━"
BOT_VERSION = "1.0"
BOT_NAME = "CodeLab"
BOT_TAGLINE = "IT ta'lim boti"
MEDALS = ["🥇", "🥈", "🥉"]


def esc(value):
    return html.escape(str(value), quote=False)


def esc_attr(value):
    return html.escape(str(value), quote=True)


def local_now():
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=TZ_OFFSET_HOURS)


def day_emoji():
    hour = local_now().hour
    if 5 <= hour < 12:
        return "🌅"
    if 12 <= hour < 18:
        return "☀️"
    if 18 <= hour < 23:
        return "🌆"
    return "🌙"


def progress_bar(done, total, width=10):
    filled = round(width * done / total) if total else 0
    return "▰" * filled + "▱" * (width - filled)


def percent(score, total):
    return round(100 * score / total) if total else 0


def mention(user_id, name):
    return f'<a href="tg://user?id={user_id}">{esc(name)}</a>'


def user_tag(user):
    """@username bo'lsa o'shani, bo'lmasa ismga havola qiladi."""
    if user.username:
        return f"@{user.username}"
    return mention(user.id, user.full_name)


def short_date(value):
    """'2026-11-14 20:12:39' -> '14.11.2026'"""
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return "-"


def medal(index):
    return MEDALS[index] if index < len(MEDALS) else f"{index + 1}."


def ai_to_html(text):
    """AI javobidagi **qalin** va `kod` belgilarini Telegram HTML'ga aylantiradi."""
    safe = esc(text)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe, flags=re.S)
    safe = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", safe)
    return safe


def header(icon, title):
    return f"{icon} <b>{esc(title)}</b>\n{LINE}\n"


def welcome_text(user, is_new, is_admin):
    greet = "Xush kelibsiz" if is_new else "Yana ko'rishganimizdan xursandmiz"
    text = (
        f"💻 <b>{BOT_NAME}</b> · {BOT_TAGLINE}\n{LINE}\n\n"
        f"{day_emoji()} <b>Assalomu alaykum, {user_tag(user)}!</b>\n"
        f"{greet}! 🤝\n\n"
        "Men IT va dasturlashni o'rganuvchi o'quvchilar uchun yaratilgan yordamchi botman. Mana nimalar qila olaman:\n\n"
        "📝 <b>Quizlar</b> — bilimingizni sinab, ball to'plang\n"
        "🏆 <b>Reyting</b> — eng kuchli o'quvchilar ro'yxati\n"
        "📢 <b>E'lonlar</b> — musobaqa va yangiliklar\n"
        "🤖 <b>AI yordamchi</b> — savollaringizga javob beradi\n"
        "✉️ <b>Murojaat</b> — adminga to'g'ridan-to'g'ri yozing\n\n"
        "<i>Boshlash uchun pastdagi menyudan tanlang</i> 👇"
    )
    if is_admin:
        text += "\n\n🛠 Siz adminsiz — boshqaruv paneli: /admin"
    return text


def about_text():
    return (
        header("ℹ️", f"{BOT_NAME} haqida")
        + f"\n<blockquote>{BOT_NAME} — IT va dasturlashni o'rganuvchi o'quvchilar uchun: bilim sinash, "
        "yangiliklardan xabardor bo'lish va savollarga tez javob olish uchun.</blockquote>\n\n"
        "📌 <b>Qoidalar</b>\n"
        "• Reytingda har quizning <b>eng yaxshi</b> natijangiz hisoblanadi\n"
        "• Savollar har safar aralashtirib beriladi\n"
        "• E'lonlar saytdagi yangiliklar bilan avtomatik yangilanadi\n\n"
        "⌨️ <b>Buyruqlar</b>\n"
        "/start — bosh menyu\n"
        "/quizlar — quizlar ro'yxati\n"
        "/profil — mening natijalarim\n"
        "/cancel — joriy amalni bekor qilish\n\n"
        f"<i>Versiya {BOT_VERSION}</i>"
    )
