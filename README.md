# CodeLab — IT ta'lim Telegram boti

Maktab o'quvchilari uchun bot: quizlar, reyting, e'lonlar (saytdan avtomatik), AI yordamchi,
adminga murojaat va to'liq admin panel.

## Imkoniyatlar

**O'quvchilar uchun**
- `/start` — shaxsiy salomlashuv (`@username` bilan), bot haqida qisqa ma'lumot, menyu
- 📝 Quizlar — savollar aralashtirib beriladi, har javobdan keyin natija, yakunda foiz va o'rin
- 🏆 Reyting — har quizning eng yaxshi natijasi hisoblanadi (qayta yechib ball "yig'ib" bo'lmaydi)
- 👤 Profil — yechilgan quizlar, jami ball, reytingdagi o'rin
- 📢 E'lonlar — so'nggi 5 ta e'lon
- 🤖 AI yordamchi — bepul AI bilan suhbat
- ✉️ Murojaat — adminga xabar yuborish, admin bot orqali javob beradi

**Adminlar uchun** (`/admin`)
- Quiz qo'shish / o'chirish (tasdiqlash bilan)
- E'lon yuborish (oldindan ko'rish va tasdiqlash bilan)
- Statistika (jami, yangi, faol foydalanuvchilar, urinishlar)
- Natijalarni CSV (Excel) ko'rinishida yuklab olish
- Murojaatlarga javob berish
- Bosh admin: boshqa adminlarni qo'shish va o'chirish

**Tizim**
- Saytdan e'lon qabul qiluvchi API (pastda)
- Spamdan himoya (tez-tez yuborilgan xabarlar o'tkazilmaydi)
- Ixtiyoriy: majburiy kanal obunasi va e'lonlarni kanalga avtomatik joylash
- Kutilmagan xatoliklarda bot to'xtamaydi, foydalanuvchiga tushunarli xabar chiqadi

## Ishga tushirish (kompyuterda)
1. `pip install -r requirements.txt`
2. `.env.example` nusxasini `.env` qiling va to'ldiring
3. `python main.py`

## Sozlamalar (`.env`)
| O'zgaruvchi | Vazifasi |
|---|---|
| `BOT_TOKEN` | @BotFather tokeni (majburiy) |
| `OWNER_ID` | Bosh admin Telegram ID si (majburiy) |
| `TZ_OFFSET_HOURS` | Vaqt zonasi (Toshkent: 5) |
| `AI_API_KEY` | Groq bepul API kaliti (console.groq.com) |
| `SITE_API_KEY` | Sayt botga e'lon yuborishi uchun maxfiy kalit |
| `DB_PATH` | Baza fayli (Railway'da `/data/bot.db`) |
| `REQUIRED_CHANNEL` | Ixtiyoriy: majburiy obuna kanali (`@kanal`) |
| `ANNOUNCE_CHANNEL` | Ixtiyoriy: e'lonlar joylanadigan kanal |

Kanal imkoniyatlari uchun bot o'sha kanalda **admin** bo'lishi kerak.

## Railway'ga joylash
1. Loyihani GitHub'ga yuklang (`.env` yuklanmaydi)
2. Railway -> New Project -> Deploy from GitHub
3. Variables bo'limiga `.env.example` dagi o'zgaruvchilarni kiriting
4. Volume qo'shing va `DB_PATH=/data/bot.db` qiling (aks holda har deployda baza o'chadi)
5. Settings -> Networking -> Generate Domain (sayt shu manzilga e'lon yuboradi)

## AI ni ulash (bepul)
Bot har qanday OpenAI formatidagi xizmat bilan ishlaydi. Uchta o'zgaruvchi kerak: `AI_API_KEY`, `AI_BASE_URL`, `AI_MODEL`.

**Variant 1 — Google Gemini** (https://aistudio.google.com)
1. Google hisobingiz bilan kiring, **Get API key** -> **Create API key**
2. `.env` ga yozing:
```
AI_API_KEY=<kalit>
AI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
AI_MODEL=gemini-3-flash-preview
AI_REASONING_EFFORT=low
```
Model nomlari tez-tez yangilanadi: AI Studio'dagi joriy "Flash" modelini tekshiring.

**Variant 2 — Groq** (https://console.groq.com): `gsk_...` kalit, boshqa o'zgaruvchilar standart holda qoladi.
Ba'zi hududlardan ro'yxatdan o'tish bloklanishi mumkin.

Tekshirish: botda «🤖 AI yordamchi» ni bosib savol yozing. «AI sozlanmagan» — kalit kiritilmagan;
«band» — bepul limit vaqtincha tugagan; boshqa xatolar sababi loglarda yoziladi (Railway -> Deployments -> Logs).

## Quiz qo'shish formati
Admin panelda «➕ Yangi quiz» ni bosing, nom yozing, so'ng savollarni shunday yuboring
(to'g'ri javob oldiga `+`):

```
Toshkent qaysi davlat poytaxti?
+O'zbekiston
Qozog'iston
Qirg'iziston
```
Har savol 2 tadan 8 tagacha variantdan iborat bo'ladi.

## Sayt bilan aloqa (e'lon yuborish)
```
POST https://<bot-manzili>/api/announcements
Header: X-API-Key: <SITE_API_KEY>
Body (JSON): {"title": "Informatika olimpiadasi", "text": "Ro'yxatdan o'tish ochildi", "url": "https://sayt.uz/olimpiada"}
```
`title` va `text` majburiy, `url` ixtiyoriy. Javob: `202 {"id": 1, "status": "queued"}`.
Xatolar: 400 (noto'g'ri ma'lumot), 401 (kalit noto'g'ri), 503 (kalit sozlanmagan).

Tekshirish:
`curl -X POST URL/api/announcements -H "X-API-Key: KALIT" -H "Content-Type: application/json" -d '{"title":"Sinov","text":"Salom"}'`

Sog'liq tekshiruvi: `GET /health`.

## Tuzilma
- `main.py` — ishga tushirish, himoya qatlamlari, bot profili
- `config.py` — sozlamalar
- `database.py` — baza bilan ishlash
- `ui.py` — matnlar va formatlash (salomlashuv, progress, HTML)
- `keyboards.py`, `states.py`, `filters.py` — tugmalar, holatlar, filtrlar
- `middlewares.py` — spam filtri, majburiy obuna
- `handlers/` — foydalanuvchi, quiz, e'lonlar, AI, admin
- `services/` — AI, e'lon tarqatish, sayt API, obuna tekshiruvi
