"""
Bot Handlers - Barcha buyruqlar va callbacklar
"""

import asyncio
import logging
import json
import os
import re
from aiogram import Router, types, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core import SmartResearcher
from config import CHANNEL_USERNAME, MAX_POST_LENGTH, ADMIN_ID, OPENAI_API_KEY
from .keyboards import get_post_keyboard

router = Router()
researcher = SmartResearcher()
logger = logging.getLogger(__name__)

# ============ SOZLAMALAR ============

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "auto_post_enabled": True,
    "post_times": ["09:00", "14:00", "20:00"],
    "topics": [
        "AI sun'iy intellekt yangiliklari",
        "Python dasturlash yangiliklar",
        "JavaScript React Angular Vue",
        "Texnologiya startup yangiliklar",
        "Kiberxavfsizlik yangiliklar"
    ],
    "timezone_offset": 5
}

# Vaqtinchalik postlar
temp_posts = {}


def load_settings() -> dict:
    """Sozlamalarni yuklash"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Sozlamalarni yuklashda xato: {e}")
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict):
    """Sozlamalarni saqlash"""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Sozlamalarni saqlashda xato: {e}")


def sanitize_html(text: str) -> str:
    """HTML teglarini tozalash va to'g'rilash"""
    if not text:
        return text

    # Ochiq teglarni yopish
    tags = ['b', 'i', 'code', 'pre', 'a']

    for tag in tags:
        # Ochiq teglar soni
        open_count = len(re.findall(f'<{tag}[^>]*>', text, re.IGNORECASE))
        # Yopiq teglar soni
        close_count = len(re.findall(f'</{tag}>', text, re.IGNORECASE))

        # Agar ochiq ko'p bo'lsa, yopamiz
        while open_count > close_count:
            text += f'</{tag}>'
            close_count += 1

    return text


# ============ STATES ============

class EditStates(StatesGroup):
    waiting_for_edit = State()
    waiting_for_time = State()
    waiting_for_topic = State()


# ============ YORDAMCHI FUNKSIYALAR ============

async def send_to_channel(bot: Bot, text: str, image_url: str = None) -> bool:
    """Kanalga post yuborish"""
    try:
        if not CHANNEL_USERNAME:
            logger.warning("CHANNEL_USERNAME sozlanmagan!")
            return False

        # HTML ni tozalash
        clean_text = sanitize_html(text)

        if image_url:
            await bot.send_photo(
                chat_id=CHANNEL_USERNAME,
                photo=image_url,
                caption=clean_text[:1024],
                parse_mode="HTML"
            )
        else:
            await bot.send_message(
                chat_id=CHANNEL_USERNAME,
                text=clean_text,
                parse_mode="HTML"
            )

        logger.info(f"Post kanalga yuborildi: {CHANNEL_USERNAME}")
        return True

    except Exception as e:
        logger.error(f"Kanalga yuborishda xatolik: {e}")
        return False


# ============ /start ============

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 <b>Salom! Men Smart Research Botman.</b>\n\n"
        "Men internetdan ma'lumot qidirib, Telegram kanal uchun post yozaman.\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📌 <b>Asosiy buyruqlar:</b>\n\n"
        "<code>/research [mavzu]</code>\n"
        "└ To'liq tadqiqot va post\n\n"
        "<code>/quick [mavzu]</code>\n"
        "└ Tezkor qisqa post\n\n"
        "<code>/compare [A] vs [B]</code>\n"
        "└ Ikki narsani solishtirish\n\n"
        "<code>/trending</code>\n"
        "└ Bugungi trendlar\n\n"
        "<code>/publish [mavzu]</code>\n"
        "└ To'g'ridan-to'g'ri kanalga\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⚙️ <b>Admin buyruqlar:</b>\n\n"
        "<code>/settings</code> - Sozlamalar\n"
        "<code>/settimes</code> - Vaqtlarni sozlash\n"
        "<code>/settopics</code> - Mavzularni sozlash\n"
        "<code>/toggle</code> - Avtomatikni yoqish/o'chirish\n"
        "<code>/status</code> - Bot holati\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Misol:</b> <code>/research React 19 yangiliklari</code>",
        parse_mode="HTML"
    )


# ============ /help ============

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📖 <b>Yordam</b>\n\n"
        "<b>1. To'liq tadqiqot:</b>\n"
        "<code>/research Python 3.13</code>\n"
        "Bot internetdan qidiradi, tahlil qiladi va post yozadi.\n\n"
        "<b>2. Tezkor post:</b>\n"
        "<code>/quick ChatGPT-5</code>\n"
        "Qisqa 2-3 jumlali post.\n\n"
        "<b>3. Solishtirish:</b>\n"
        "<code>/compare React vs Vue</code>\n"
        "Ikki texnologiyani taqqoslash.\n\n"
        "<b>4. Trendlar:</b>\n"
        "<code>/trending</code>\n"
        "Bugungi IT yangiliklarini ko'rsatadi.\n\n"
        "<b>5. Kanalga yuborish:</b>\n"
        "<code>/publish AI yangiliklar</code>\n"
        "Post tayyorlab to'g'ridan-to'g'ri kanalga yuboradi.",
        parse_mode="HTML"
    )


# ============ /settings ============

@router.message(Command("settings"))
async def cmd_settings(message: types.Message):
    settings = load_settings()

    times_str = ", ".join(settings["post_times"])
    topics_str = "\n".join([f"   {i + 1}. {t}" for i, t in enumerate(settings["topics"])])
    status = "✅ Yoqilgan" if settings["auto_post_enabled"] else "❌ O'chirilgan"

    await message.answer(
        f"⚙️ <b>Bot sozlamalari</b>\n\n"
        f"<b>Avtomatik posting:</b> {status}\n\n"
        f"<b>⏰ Post vaqtlari (Toshkent):</b>\n   {times_str}\n\n"
        f"<b>📝 Mavzular:</b>\n{topics_str}\n\n"
        f"<b>📢 Kanal:</b> {CHANNEL_USERNAME}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<code>/settimes</code> - Vaqtlarni o'zgartirish\n"
        f"<code>/settopics</code> - Mavzularni o'zgartirish\n"
        f"<code>/toggle</code> - Yoqish/O'chirish",
        parse_mode="HTML"
    )


# ============ /status ============

@router.message(Command("status"))
async def cmd_status(message: types.Message):
    settings = load_settings()

    auto_status = "✅ Ishlayapti" if settings["auto_post_enabled"] else "⏸ To'xtatilgan"
    times = ", ".join(settings["post_times"])
    topics_count = len(settings["topics"])

    await message.answer(
        f"📊 <b>Bot holati</b>\n\n"
        f"🤖 <b>Bot:</b> ✅ Online\n"
        f"📢 <b>Kanal:</b> {CHANNEL_USERNAME}\n"
        f"🔄 <b>Avtomatik:</b> {auto_status}\n"
        f"⏰ <b>Vaqtlar:</b> {times}\n"
        f"📝 <b>Mavzular:</b> {topics_count} ta",
        parse_mode="HTML"
    )


# ============ /toggle ============

@router.message(Command("toggle"))
async def cmd_toggle(message: types.Message):
    settings = load_settings()
    settings["auto_post_enabled"] = not settings["auto_post_enabled"]
    save_settings(settings)

    if settings["auto_post_enabled"]:
        status = "✅ <b>Avtomatik posting YOQILDI!</b>\n\nBot belgilangan vaqtlarda post chiqaradi."
    else:
        status = "❌ <b>Avtomatik posting O'CHIRILDI!</b>\n\nBot faqat buyruq bilan ishlaydi."

    await message.answer(status, parse_mode="HTML")


# ============ /settimes ============

@router.message(Command("settimes"))
async def cmd_settimes(message: types.Message, state: FSMContext):
    settings = load_settings()
    current = ", ".join(settings["post_times"])

    await message.answer(
        f"⏰ <b>Vaqtlarni sozlash</b>\n\n"
        f"Hozirgi vaqtlar:\n<code>{current}</code>\n\n"
        f"Yangi vaqtlarni yozing (vergul bilan ajratib):\n\n"
        f"Misol: <code>09:00, 13:00, 18:00, 21:00</code>\n\n"
        f"❌ Bekor qilish: /cancel",
        parse_mode="HTML"
    )
    await state.set_state(EditStates.waiting_for_time)


@router.message(EditStates.waiting_for_time)
async def process_settimes(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Bekor qilindi")
        return

    try:
        times = [t.strip() for t in message.text.split(",")]

        valid_times = []
        for t in times:
            if ":" not in t:
                raise ValueError(f"Noto'g'ri format: {t}")

            parts = t.split(":")
            hour = int(parts[0])
            minute = int(parts[1])

            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError(f"Noto'g'ri vaqt: {t}")

            valid_times.append(f"{hour:02d}:{minute:02d}")

        settings = load_settings()
        settings["post_times"] = valid_times
        save_settings(settings)

        await message.answer(
            f"✅ <b>Vaqtlar saqlandi!</b>\n\n"
            f"Yangi vaqtlar: <code>{', '.join(valid_times)}</code>\n\n"
            f"Bot shu vaqtlarda avtomatik post chiqaradi.",
            parse_mode="HTML"
        )

    except ValueError as e:
        await message.answer(
            f"❌ <b>Xatolik:</b> {e}\n\n"
            f"To'g'ri format: <code>09:00, 14:00, 20:00</code>",
            parse_mode="HTML"
        )

    await state.clear()


# ============ /settopics ============

@router.message(Command("settopics"))
async def cmd_settopics(message: types.Message, state: FSMContext):
    settings = load_settings()
    current = "\n".join([f"{i + 1}. {t}" for i, t in enumerate(settings["topics"])])

    await message.answer(
        f"📝 <b>Mavzularni sozlash</b>\n\n"
        f"Hozirgi mavzular:\n<code>{current}</code>\n\n"
        f"Yangi mavzularni yozing.\n"
        f"Har bir qator - bitta mavzu:\n\n"
        f"Misol:\n"
        f"<code>AI sun'iy intellekt\n"
        f"Python dasturlash\n"
        f"JavaScript React Vue\n"
        f"Startup texnologiya</code>\n\n"
        f"❌ Bekor qilish: /cancel",
        parse_mode="HTML"
    )
    await state.set_state(EditStates.waiting_for_topic)


@router.message(EditStates.waiting_for_topic)
async def process_settopics(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Bekor qilindi")
        return

    topics = [t.strip() for t in message.text.split("\n") if t.strip()]

    if not topics:
        await message.answer("❌ Kamida 1 ta mavzu kiriting!")
        return

    settings = load_settings()
    settings["topics"] = topics
    save_settings(settings)

    topics_str = "\n".join([f"   {i + 1}. {t}" for i, t in enumerate(topics)])
    await message.answer(
        f"✅ <b>Mavzular saqlandi!</b>\n\n"
        f"<b>Yangi mavzular ({len(topics)} ta):</b>\n{topics_str}",
        parse_mode="HTML"
    )

    await state.clear()


# ============ /research ============

@router.message(Command("research"))
async def cmd_research(message: types.Message):
    topic = message.text.replace("/research", "").strip()

    if not topic:
        await message.answer(
            "❌ <b>Mavzuni yozing!</b>\n\n"
            "✅ Misol: <code>/research React 19 yangiliklari</code>",
            parse_mode="HTML"
        )
        return

    status_msg = await message.answer(
        f"🔍 <b>Qidirilmoqda:</b> {topic}\n\n"
        f"⏳ Internetdan ma'lumot yig'ilmoqda...",
        parse_mode="HTML"
    )

    try:
        await asyncio.sleep(2)
        await status_msg.edit_text(
            f"🔍 <b>Mavzu:</b> {topic}\n\n"
            f"📖 Maqolalar tahlil qilinmoqda...",
            parse_mode="HTML"
        )

        result = await researcher.full_research(topic, with_image=True)

        if not result["success"]:
            await status_msg.edit_text(
                f"❌ <b>Xatolik:</b> {result.get('error', 'Nomalum xato')}",
                parse_mode="HTML"
            )
            return

        await status_msg.edit_text(
            f"🔍 <b>Mavzu:</b> {topic}\n\n"
            f"🧠 Post yozilmoqda...",
            parse_mode="HTML"
        )

        post = sanitize_html(result["post"])

        if len(post) > MAX_POST_LENGTH:
            post = post[:MAX_POST_LENGTH] + "\n\n...(davomi kesildi)"

        post_id = str(message.message_id)
        temp_posts[post_id] = {
            "topic": topic,
            "post": post,
            "image_url": result.get("image_url"),
            "has_image": bool(result.get("image_url"))
        }

        if result.get("image_url"):
            await status_msg.delete()
            await message.answer_photo(
                photo=result["image_url"],
                caption=f"✅ <b>Tayyor!</b>\n\n{post[:900]}",
                parse_mode="HTML",
                reply_markup=get_post_keyboard(post_id)
            )
        else:
            await status_msg.edit_text(
                f"✅ <b>Tayyor!</b>\n\n{post}",
                parse_mode="HTML",
                reply_markup=get_post_keyboard(post_id)
            )

    except Exception as e:
        logger.error(f"Research xatolik: {e}")
        await status_msg.edit_text(
            f"❌ <b>Xatolik yuz berdi:</b>\n<code>{str(e)}</code>",
            parse_mode="HTML"
        )


# ============ /publish ============

@router.message(Command("publish"))
async def cmd_publish(message: types.Message, bot: Bot):
    topic = message.text.replace("/publish", "").strip()

    if not topic:
        await message.answer(
            "❌ <b>Mavzuni yozing!</b>\n\n"
            "✅ Misol: <code>/publish AI yangiliklari</code>",
            parse_mode="HTML"
        )
        return

    status_msg = await message.answer(
        f"🚀 <b>Kanalga tayyorlanmoqda:</b>\n{topic}\n\n"
        f"⏳ Biroz kuting...",
        parse_mode="HTML"
    )

    try:
        result = await researcher.full_research(topic, with_image=True)

        if not result["success"]:
            await status_msg.edit_text(
                f"❌ <b>Xatolik:</b> {result.get('error')}",
                parse_mode="HTML"
            )
            return

        success = await send_to_channel(bot, result["post"], result.get("image_url"))

        if success:
            await status_msg.edit_text(
                f"✅ <b>Post kanalga yuborildi!</b>\n\n"
                f"📢 Kanal: {CHANNEL_USERNAME}\n"
                f"📝 Mavzu: {topic}",
                parse_mode="HTML"
            )
        else:
            await status_msg.edit_text(
                f"❌ <b>Kanalga yuborib bo'lmadi!</b>\n\n"
                f"Tekshiring:\n"
                f"• Bot kanalda admin ekanligini\n"
                f"• CHANNEL_USERNAME to'g'ri yozilganini",
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"Publish xatolik: {e}")
        await status_msg.edit_text(f"❌ <b>Xatolik:</b> {str(e)}", parse_mode="HTML")


# ============ /quick ============

@router.message(Command("quick"))
async def cmd_quick(message: types.Message):
    topic = message.text.replace("/quick", "").strip()

    if not topic:
        await message.answer(
            "❌ <b>Mavzuni yozing!</b>\n\n"
            "✅ Misol: <code>/quick GPT-5</code>",
            parse_mode="HTML"
        )
        return

    status_msg = await message.answer("⚡ Tezkor post tayyorlanmoqda...")

    try:
        result = await researcher.quick_post(topic)

        if result["success"]:
            post = sanitize_html(result["post"])
            post_id = str(message.message_id)
            temp_posts[post_id] = {
                "topic": topic,
                "post": post,
                "has_image": False
            }

            await status_msg.edit_text(
                f"⚡ <b>Tezkor post:</b>\n\n{post}",
                parse_mode="HTML",
                reply_markup=get_post_keyboard(post_id)
            )
        else:
            await status_msg.edit_text("❌ Xatolik yuz berdi")

    except Exception as e:
        logger.error(f"Quick xatolik: {e}")
        await status_msg.edit_text(f"❌ <b>Xatolik:</b> {str(e)}", parse_mode="HTML")


# ============ /compare ============

@router.message(Command("compare"))
async def cmd_compare(message: types.Message):
    text = message.text.replace("/compare", "").strip()

    if " vs " not in text.lower():
        await message.answer(
            "❌ <b>Noto'g'ri format!</b>\n\n"
            "✅ To'g'ri: <code>/compare React vs Vue</code>",
            parse_mode="HTML"
        )
        return

    parts = text.split(" vs " if " vs " in text else " VS ")
    if len(parts) != 2:
        await message.answer("❌ Faqat 2 ta narsa bo'lishi kerak!")
        return

    topic1 = parts[0].strip()
    topic2 = parts[1].strip()

    status_msg = await message.answer(
        f"⚔️ <b>{topic1}</b> vs <b>{topic2}</b>\n\n"
        f"⏳ Solishtirilmoqda...",
        parse_mode="HTML"
    )

    try:
        result = await researcher.compare_topics(topic1, topic2)

        if result["success"]:
            post = sanitize_html(result["post"])
            post_id = str(message.message_id)
            temp_posts[post_id] = {
                "topic": f"{topic1} vs {topic2}",
                "post": post,
                "has_image": False
            }

            await status_msg.edit_text(
                post,
                parse_mode="HTML",
                reply_markup=get_post_keyboard(post_id)
            )
        else:
            await status_msg.edit_text("❌ Xatolik yuz berdi")

    except Exception as e:
        logger.error(f"Compare xatolik: {e}")
        await status_msg.edit_text(f"❌ <b>Xatolik:</b> {str(e)}", parse_mode="HTML")


# ============ /trending ============

@router.message(Command("trending"))
async def cmd_trending(message: types.Message):
    status_msg = await message.answer("🔥 Trendlar qidirilmoqda...")

    try:
        result = await researcher.get_trending()

        if result["success"]:
            post = sanitize_html(result["post"])
            temp_posts["trending"] = {
                "topic": "Bugungi trendlar",
                "post": post,
                "has_image": False
            }

            await status_msg.edit_text(
                post,
                parse_mode="HTML",
                reply_markup=get_post_keyboard("trending")
            )
        else:
            await status_msg.edit_text("❌ Xatolik yuz berdi")

    except Exception as e:
        logger.error(f"Trending xatolik: {e}")
        await status_msg.edit_text(f"❌ <b>Xatolik:</b> {str(e)}", parse_mode="HTML")


# ============ CALLBACK: Kanalga yuborish ============

@router.callback_query(F.data.startswith("publish:"))
async def callback_publish(callback: types.CallbackQuery, bot: Bot):
    post_id = callback.data.split(":")[1]

    if post_id not in temp_posts:
        await callback.answer("❌ Post topilmadi!", show_alert=True)
        return

    data = temp_posts[post_id]

    await callback.answer("📤 Kanalga yuborilmoqda...")

    success = await send_to_channel(bot, data["post"], data.get("image_url"))

    if success:
        # Tugmalarni olib tashlash
        try:
            if data.get("has_image"):
                await callback.message.edit_caption(
                    caption=callback.message.caption,
                    reply_markup=None
                )
            else:
                await callback.message.edit_reply_markup(reply_markup=None)
        except:
            pass

        await callback.message.answer(
            f"✅ <b>Post kanalga yuborildi!</b>\n"
            f"📢 {CHANNEL_USERNAME}",
            parse_mode="HTML"
        )
    else:
        await callback.answer(
            "❌ Yuborib bo'lmadi!\nBot kanalda admin ekanligini tekshiring.",
            show_alert=True
        )


# ============ CALLBACK: Qayta yozish ============

@router.callback_query(F.data.startswith("regenerate:"))
async def callback_regenerate(callback: types.CallbackQuery):
    post_id = callback.data.split(":")[1]

    if post_id not in temp_posts:
        await callback.answer("❌ Post topilmadi!", show_alert=True)
        return

    topic = temp_posts[post_id]["topic"]
    has_image = temp_posts[post_id].get("has_image", False)

    await callback.answer("🔄 Qayta yozilmoqda... (15-20 soniya)")

    try:
        result = await researcher.full_research(topic, with_image=False)

        if result["success"]:
            post = sanitize_html(result["post"])
            temp_posts[post_id]["post"] = post

            # Rasmli post bo'lsa, caption ni o'zgartirish
            if has_image:
                await callback.message.edit_caption(
                    caption=f"✅ <b>Qayta yozildi!</b>\n\n{post[:900]}",
                    parse_mode="HTML",
                    reply_markup=get_post_keyboard(post_id)
                )
            else:
                await callback.message.edit_text(
                    f"✅ <b>Qayta yozildi!</b>\n\n{post}",
                    parse_mode="HTML",
                    reply_markup=get_post_keyboard(post_id)
                )
        else:
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)

    except Exception as e:
        logger.error(f"Regenerate xatolik: {e}")
        try:
            await callback.answer(f"❌ Xatolik!", show_alert=True)
        except:
            pass


# ============ CALLBACK: Bekor qilish ============

@router.callback_query(F.data.startswith("cancel:"))
async def callback_cancel(callback: types.CallbackQuery):
    post_id = callback.data.split(":")[1]

    if post_id in temp_posts:
        del temp_posts[post_id]

    await callback.answer("❌ Bekor qilindi")

    try:
        await callback.message.delete()
    except:
        pass


# ============ CALLBACK: Tahrirlash ============

@router.callback_query(F.data.startswith("edit:"))
async def callback_edit(callback: types.CallbackQuery, state: FSMContext):
    post_id = callback.data.split(":")[1]

    if post_id not in temp_posts:
        await callback.answer("❌ Post topilmadi!", show_alert=True)
        return

    await callback.answer()
    await state.update_data(post_id=post_id)
    await state.set_state(EditStates.waiting_for_edit)

    await callback.message.answer(
        "✏️ <b>Tahrirlash</b>\n\n"
        "Nimani o'zgartirmoqchisiz? Yozing:\n\n"
        "Misollar:\n"
        "• Sarlavhani qisqartir\n"
        "• Ko'proq emoji qo'sh\n"
        "• Rasmiyroq qil\n"
        "• Inglizcha atamalarni tushuntir\n\n"
        "❌ Bekor qilish: /cancel",
        parse_mode="HTML"
    )


@router.message(EditStates.waiting_for_edit)
async def process_edit(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Bekor qilindi")
        return

    data = await state.get_data()
    post_id = data.get("post_id")

    if not post_id or post_id not in temp_posts:
        await state.clear()
        await message.answer("❌ Post topilmadi!")
        return

    original_post = temp_posts[post_id]["post"]
    edit_request = message.text

    status_msg = await message.answer("✏️ Tahrirlanmoqda...")

    try:
        from openai import AsyncOpenAI

        edit_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

        response = await edit_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Sen matn tahrirlovchisisan. Postni so'rov bo'yicha tahrirlash. HTML formatni to'g'ri saqlash - har bir ochilgan teg yopilishi kerak (<b></b>, <i></i>, <code></code>). Faqat tahrirlangan postni qaytar, boshqa hech narsa yozma."
                },
                {
                    "role": "user",
                    "content": f"POST:\n{original_post}\n\nSO'ROV: {edit_request}"
                }
            ],
            temperature=0.7
        )

        edited_post = sanitize_html(response.choices[0].message.content)
        temp_posts[post_id]["post"] = edited_post

        await status_msg.edit_text(
            f"✅ <b>Tahrirlandi!</b>\n\n{edited_post}",
            parse_mode="HTML",
            reply_markup=get_post_keyboard(post_id)
        )

    except Exception as e:
        logger.error(f"Edit xatolik: {e}")
        await status_msg.edit_text(f"❌ <b>Xatolik:</b> {str(e)}", parse_mode="HTML")

    await state.clear()