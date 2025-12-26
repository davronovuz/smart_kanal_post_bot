"""
Smart Research Bot - Asosiy fayl
Telegram bot + OpenAI web search

Ishlatish:
1. .env faylni sozlang (BOT_TOKEN, OPENAI_API_KEY)
2. pip install -r requirements.txt
3. python main.py
"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from bot import router

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


async def main():
    """Botni ishga tushirish"""

    # Token tekshiruvi
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN topilmadi! .env faylni tekshiring.")
        return

    # Bot yaratish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Dispatcher yaratish
    dp = Dispatcher()

    # Routerlarni ulash
    dp.include_router(router)

    # Startup xabar
    logger.info("🚀 Smart Research Bot ishga tushmoqda...")

    try:
        # Oldingi xabarlarni o'tkazib yuborish
        await bot.delete_webhook(drop_pending_updates=True)

        # Pollingni boshlash
        logger.info("✅ Bot tayyor! Telegram'ga o'ting va /start bosing.")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"❌ Xatolik: {e}")

    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi.")