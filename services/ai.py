import logging

import httpx

from config import AI_API_KEY, AI_BASE_URL, AI_MODEL, AI_REASONING_EFFORT

SYSTEM_PROMPT = (
    "Sen CodeLab botining yordamchisisan: IT va dasturlashni o'rganayotgan maktab o'quvchilariga "
    "yordam berasan. Javoblarni o'zbek tilida, qisqa, sodda va misollar bilan yoz. "
    "Kod so'ralsa, qisqa kod namunasi va izohini ber. Uy vazifasini shunchaki yechib berma, "
    "avval tushuntir."
)


async def ask(history):
    """history: [{"role": "user"|"assistant", "content": "..."}, ...]"""
    if not AI_API_KEY:
        return "AI hozircha sozlanmagan (AI_API_KEY kiritilmagan)."

    payload = {
        "model": AI_MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + history,
        "temperature": 0.6,
        "max_tokens": 1500,
    }
    if AI_REASONING_EFFORT:
        payload["reasoning_effort"] = AI_REASONING_EFFORT
    headers = {"Authorization": f"Bearer {AI_API_KEY}"}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{AI_BASE_URL.rstrip('/')}/chat/completions", json=payload, headers=headers
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"].get("content") or ""
            return content.strip() or "AI bo'sh javob qaytardi. Savolni boshqacha yozib ko'ring."
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        # sabab loglarda ko'rinadi (Railway -> Deployments -> Logs)
        logging.error("AI xatosi %s: %s", status, e.response.text[:300])
        if status == 429:
            return "AI hozir band (bepul limit tugadi). Bir ozdan keyin qayta urinib ko'ring."
        return "AI bilan bog'lanishda muammo bor. Keyinroq urinib ko'ring."
    except (httpx.HTTPError, KeyError, IndexError):
        logging.exception("AI ga ulanib bo'lmadi")
        return "Xizmatga ulanib bo'lmadi, birozdan keyin qayta urinib ko'ring."
