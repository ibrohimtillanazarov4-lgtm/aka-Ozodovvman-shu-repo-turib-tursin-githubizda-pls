import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
DB_PATH = os.getenv("DB_PATH", "bot.db")

# Mahalliy vaqt UTC'dan necha soat farq qiladi (Toshkent: 5)
TZ_OFFSET_HOURS = int(os.getenv("TZ_OFFSET_HOURS", "5"))

# Bepul sun'iy intellekt (Groq)
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.groq.com/openai/v1")
AI_MODEL = os.getenv("AI_MODEL", "llama-3.1-8b-instant")
# Ixtiyoriy (Gemini uchun "low" tavsiya etiladi): modelning o'ylash darajasi
AI_REASONING_EFFORT = os.getenv("AI_REASONING_EFFORT", "").strip()

# Sayt bilan aloqa: sayt shu kalit bilan botga e'lon yuboradi
SITE_API_KEY = os.getenv("SITE_API_KEY", "")
PORT = int(os.getenv("PORT", "8080"))

# Ixtiyoriy: majburiy obuna kanali (@kanal_nomi yoki -100...). Bot kanalda admin bo'lishi kerak.
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "").strip()
# Ixtiyoriy: kanal havolasi (kanal ID bilan berilgan bo'lsa kerak bo'ladi)
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "").strip()
# Ixtiyoriy: e'lonlar avtomatik joylanadigan kanal (@kanal_nomi yoki -100...)
ANNOUNCE_CHANNEL = os.getenv("ANNOUNCE_CHANNEL", "").strip()
