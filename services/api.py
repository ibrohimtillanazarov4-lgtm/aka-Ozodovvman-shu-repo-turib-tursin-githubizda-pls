"""Sayt uchun kichik API: sayt shu orqali botga e'lon yuboradi."""
import asyncio
import hmac
import logging

from aiohttp import web

import database as db
from services.broadcast import publish_announcement

MAX_TITLE = 200
MAX_TEXT = 3500  # Telegram xabari 4096 belgidan oshmasligi kerak


def _error(message, status):
    return web.json_response({"error": message}, status=status)


async def health(request):
    return web.json_response({"status": "ok"})


async def _broadcast(bot, title, text, url):
    try:
        sent, failed = await publish_announcement(bot, title, text, url)
        logging.info("E'lon yuborildi: %s, yetib bormadi: %s", sent, failed)
    except Exception:
        logging.exception("E'lonni tarqatishda xatolik")


async def create_announcement(request):
    api_key = request.app["api_key"]
    if not api_key:
        return _error("API o'chirilgan (SITE_API_KEY kiritilmagan)", 503)

    given = request.headers.get("X-API-Key", "")
    if not hmac.compare_digest(given.encode(), api_key.encode()):
        return _error("Kalit noto'g'ri", 401)

    try:
        data = await request.json()
    except Exception:
        return _error("JSON noto'g'ri", 400)
    if not isinstance(data, dict):
        return _error("JSON obyekt bo'lishi kerak", 400)

    title = str(data.get("title") or "").strip()
    text = str(data.get("text") or "").strip()
    url = str(data.get("url") or "").strip() or None

    if not title or len(title) > MAX_TITLE:
        return _error(f"title majburiy (ko'pi bilan {MAX_TITLE} belgi)", 400)
    if not text or len(text) > MAX_TEXT:
        return _error(f"text majburiy (ko'pi bilan {MAX_TEXT} belgi)", 400)
    if url and not url.startswith(("http://", "https://")):
        return _error("url http:// yoki https:// bilan boshlanishi kerak", 400)

    ann_id = await db.add_announcement(title, text, url)

    # javobni kutdirmaslik uchun tarqatish fonda ketadi
    task = asyncio.create_task(_broadcast(request.app["bot"], title, text, url))
    request.app["tasks"].add(task)
    task.add_done_callback(request.app["tasks"].discard)

    return web.json_response({"id": ann_id, "status": "queued"}, status=202)


def create_app(bot, api_key):
    app = web.Application()
    app["bot"] = bot
    app["api_key"] = api_key
    app["tasks"] = set()
    app.add_routes(
        [
            web.get("/health", health),
            web.post("/api/announcements", create_announcement),
        ]
    )
    return app
