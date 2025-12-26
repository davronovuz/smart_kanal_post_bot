import asyncio
from aiogram import Router, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core import SmartResearcher
from config import CHANNEL_USERNAME, MAX_POST_LENGTH
from .keyboards import get_post_keyboard, get_confirm_keyboard, get_category_keyboard

router = Router()
researcher = SmartResearcher()

# Vaqtinchalik post saqlash (keyinchalik Redis/DB ga o'tkazish mumkin)
temp_posts = {}


class EditStates(StatesGroup):
    waiting_for_edit = State()


# ============ START ============
@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 <b>Salom! Men Smart Research Botman.</b>\n\n"
        "Men internetdan ma'lumot qidirib, Telegram uchun tayyor post yozib beraman.\n\n"
        "📌 <b>Buyruqlar:</b>\n"
        "/research [mavzu] - To'liq tadqiqot va post\n"
        "/quick [mavzu] - Tezkor qisqa post\n"
        "/compare [A] vs [B] - Solishtirish\n"
        "/trending - Bugungi trendlar\n"
        "/help - Yordam\n\n"
        "💡 <b>Misol:</b> <code>/research React 19 yangiliklari</code>",
        parse_mode="HTML"
    )


# ============ HELP ============
@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📖 <b>Qo'llanma</b>\n\n"
        "<b>1. To'liq tadqiqot:</b>\n"
        "<code>/research Python 3.13 yangiliklari</code>\n"
        "Bot internetdan qidiradi va professional post yozadi.\n\n"
        "<b>2. Tezkor post:</b>\n"
        "<code>/quick ChatGPT-5</code>\n"
        "Qisqa, lo'nda post (100 so'zgacha).\n\n"
        "<b>3. Solishtirish:</b>\n"
        "<code>/compare React vs Vue</code>\n"
        "Ikki texnologiyani taqqoslash.\n\n"
        "<b>4. Trendlar:</b>\n"
        "<code>/trending</code>\n"
        "Bugungi IT trendlari.\n\n"
        "❓ Savollar bo'lsa: @admin_username",
        parse_mode="HTML"
    )


# ============ RESEARCH (Asosiy) ============
@router.message(Command("research"))
async def cmd_research(message: types.Message):
    topic = message.text.replace("/research", "").strip()

    if not topic:
        await message.answer(
            "❌ Mavzuni yozing!\n\n"
            "✅ To'g'ri: <code>/research React 19 yangiliklari</code>",
            parse_mode="HTML"
        )
        return

    # Status xabari
    status_msg = await message.answer(
        f"🔍 <b>Qidirilmoqda:</b> {topic}\n\n"
        "⏳ Internetdan ma'lumot yig'ilmoqda...",
        parse_mode="HTML"
    )

    try:
        # Status yangilash
        await asyncio.sleep(1)
        await status_msg.edit_text(
            f"🔍 <b>Mavzu:</b> {topic}\n\n"
            "📖 Maqolalar o'qilmoqda...",
            parse_mode="HTML"
        )

        # Tadqiqot
        result = await researcher.full_research(topic)

        if not result["success"]:
            await status_msg.edit_text(f"❌ Xatolik: {result.get('error', 'Nomalum xato')}")
            return

        # Status yangilash
        await status_msg.edit_text(
            f"🔍 <b>Mavzu:</b> {topic}\n\n"
            "🧠 Post yozilmoqda...",
            parse_mode="HTML"
        )

        post = result["post"]

        # Post uzunligini tekshirish
        if len(post) > MAX_POST_LENGTH:
            post = post[:MAX_POST_LENGTH] + "\n\n...(davomi kesildi)"

        # Vaqtinchalik saqlash
        post_id = str(message.message_id)
        temp_posts[post_id] = {
            "topic": topic,
            "post": post,
            "research": result["research"]
        }

        # Natijani ko'rsatish
        await status_msg.edit_text(
            f"✅ <b>Tayyor!</b>\n\n{post}",
            parse_mode="HTML",
            reply_markup=get_post_keyboard(post_id)
        )

    except Exception as e:
        await status_msg.edit_text(f"❌ Xatolik yuz berdi:\n<code>{str(e)}</code>", parse_mode="HTML")


# ============ QUICK ============
@router.message(Command("quick"))
async def cmd_quick(message: types.Message):
    topic = message.text.replace("/quick", "").strip()

    if not topic:
        await message.answer("❌ Mavzuni yozing!\n✅ Misol: <code>/quick GPT-5</code>", parse_mode="HTML")
        return

    status_msg = await message.answer("⚡ Tezkor post tayyorlanmoqda...")

    try:
        result = await researcher.quick_post(topic)

        if result["success"]:
            post_id = str(message.message_id)
            temp_posts[post_id] = {"topic": topic, "post": result["post"]}

            await status_msg.edit_text(
                f"⚡ <b>Tezkor post:</b>\n\n{result['post']}",
                parse_mode="HTML",
                reply_markup=get_post_keyboard(post_id)
            )
        else:
            await status_msg.edit_text("❌ Xatolik yuz berdi")

    except Exception as e:
        await status_msg.edit_text(f"❌ Xatolik: {str(e)}")


# ============ COMPARE ============
@router.message(Command("compare"))
async def cmd_compare(message: types.Message):
    text = message.text.replace("/compare", "").strip()

    # "vs" bilan ajratish
    if " vs " not in text.lower():
        await message.answer(
            "❌ Noto'g'ri format!\n\n"
            "✅ To'g'ri: <code>/compare React vs Vue</code>",
            parse_mode="HTML"
        )
        return

    parts = text.lower().split(" vs ")
    if len(parts) != 2:
        await message.answer("❌ Faqat 2 ta texnologiya bo'lishi kerak!")
        return

    topic1, topic2 = parts[0].strip(), parts[1].strip()

    status_msg = await message.answer(f"⚔️ <b>{topic1}</b> vs <b>{topic2}</b>\n\n⏳ Solishtirilmoqda...",
                                      parse_mode="HTML")

    try:
        result = await researcher.compare_topics(topic1, topic2)

        if result["success"]:
            post_id = str(message.message_id)
            temp_posts[post_id] = {"topic": f"{topic1} vs {topic2}", "post": result["post"]}

            await status_msg.edit_text(
                result["post"],
                parse_mode="HTML",
                reply_markup=get_post_keyboard(post_id)
            )
        else:
            await status_msg.edit_text("❌ Xatolik yuz berdi")

    except Exception as e:
        await status_msg.edit_text(f"❌ Xatolik: {str(e)}")


# ============ TRENDING ============
@router.message(Command("trending"))
async def cmd_trending(message: types.Message):
    status_msg = await message.answer("🔥 Trendlar qidirilmoqda...")

    try:
        result = await researcher.get_trending()

        if result["success"]:
            await status_msg.edit_text(
                result["post"],
                parse_mode="HTML",
                reply_markup=get_post_keyboard("trending")
            )
        else:
            await status_msg.edit_text("❌ Xatolik yuz berdi")

    except Exception as e:
        await status_msg.edit_text(f"❌ Xatolik: {str(e)}")


# ============ CALLBACK HANDLERS ============

@router.callback_query(F.data.startswith("publish:"))
async def callback_publish(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=get_confirm_keyboard())


@router.callback_query(F.data == "confirm_publish")
async def callback_confirm_publish(callback: types.CallbackQuery):
    await callback.answer("✅ Post nashr qilindi!", show_alert=True)

    # Tugmalarni olib tashlash
    await callback.message.edit_reply_markup(reply_markup=None)

    # TODO: Kanalga yuborish (CHANNEL_USERNAME mavjud bo'lsa)
    # if CHANNEL_USERNAME:
    #     await bot.send_message(CHANNEL_USERNAME, callback.message.text)


@router.callback_query(F.data == "cancel_publish")
async def callback_cancel_publish(callback: types.CallbackQuery):
    await callback.answer("Bekor qilindi")
    post_id = callback.message.message_id
    await callback.message.edit_reply_markup(reply_markup=get_post_keyboard(str(post_id)))


@router.callback_query(F.data.startswith("regenerate:"))
async def callback_regenerate(callback: types.CallbackQuery):
    post_id = callback.data.split(":")[1]

    if post_id in temp_posts:
        topic = temp_posts[post_id]["topic"]
        await callback.answer("🔄 Qayta yozilmoqda...")

        # Yangi post
        result = await researcher.full_research(topic)

        if result["success"]:
            temp_posts[post_id]["post"] = result["post"]
            await callback.message.edit_text(
                f"✅ <b>Qayta yozildi!</b>\n\n{result['post']}",
                parse_mode="HTML",
                reply_markup=get_post_keyboard(post_id)
            )
    else:
        await callback.answer("❌ Post topilmadi", show_alert=True)


@router.callback_query(F.data.startswith("cancel:"))
async def callback_cancel(callback: types.CallbackQuery):
    await callback.answer("❌ Bekor qilindi")
    await callback.message.delete()


@router.callback_query(F.data.startswith("edit:"))
async def callback_edit(callback: types.CallbackQuery, state: FSMContext):
    post_id = callback.data.split(":")[1]
    await callback.answer()

    await state.update_data(post_id=post_id)
    await state.set_state(EditStates.waiting_for_edit)

    await callback.message.answer(
        "✏️ <b>Tahrirlash</b>\n\n"
        "Nimani o'zgartirmoqchisiz? Yozing:\n"
        "Masalan: <i>\"Sarlavhani qisqartir\"</i> yoki <i>\"Emoji qo'sh\"</i>",
        parse_mode="HTML"
    )


@router.message(EditStates.waiting_for_edit)
async def process_edit(message: types.Message, state: FSMContext):
    data = await state.get_data()
    post_id = data.get("post_id")

    if post_id and post_id in temp_posts:
        original_post = temp_posts[post_id]["post"]
        edit_request = message.text

        status_msg = await message.answer("✏️ Tahrirlanmoqda...")

        try:
            # OpenAI bilan tahrirlash
            from openai import AsyncOpenAI
            from config import OPENAI_API_KEY

            client = AsyncOpenAI(api_key=OPENAI_API_KEY)

            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system",
                     "content": "Sen matn tahrirlovchisisan. Postni so'rov bo'yicha tahrirlash. Formatni saqlash. Faqat tahrirlangan postni qaytar."},
                    {"role": "user", "content": f"POST:\n{original_post}\n\nSO'ROV: {edit_request}"}
                ]
            )

            edited_post = response.choices[0].message.content
            temp_posts[post_id]["post"] = edited_post

            await status_msg.edit_text(
                f"✅ <b>Tahrirlandi!</b>\n\n{edited_post}",
                parse_mode="HTML",
                reply_markup=get_post_keyboard(post_id)
            )

        except Exception as e:
            await status_msg.edit_text(f"❌ Xatolik: {str(e)}")

    await state.clear()