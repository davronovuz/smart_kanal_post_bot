from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_post_keyboard(post_id: str = "0") -> InlineKeyboardMarkup:
    """Post ostidagi tugmalar"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Nashr qilish", callback_data=f"publish:{post_id}"),
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"edit:{post_id}"),
        ],
        [
            InlineKeyboardButton(text="🔄 Qayta yozish", callback_data=f"regenerate:{post_id}"),
            InlineKeyboardButton(text="❌ Bekor", callback_data=f"cancel:{post_id}"),
        ]
    ])


def get_edit_keyboard(post_id: str = "0") -> InlineKeyboardMarkup:
    """Tahrirlash tugmalari"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Qisqartirish", callback_data=f"shorten:{post_id}"),
            InlineKeyboardButton(text="📝 Kengaytirish", callback_data=f"expand:{post_id}"),
        ],
        [
            InlineKeyboardButton(text="🎨 Emoji qo'shish", callback_data=f"emoji:{post_id}"),
            InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"back:{post_id}"),
        ]
    ])


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Tasdiqlash tugmasi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, nashr qil", callback_data="confirm_publish"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data="cancel_publish"),
        ]
    ])


def get_category_keyboard() -> InlineKeyboardMarkup:
    """Kategoriya tanlash"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💻 Frontend", callback_data="cat:frontend"),
            InlineKeyboardButton(text="⚙️ Backend", callback_data="cat:backend"),
        ],
        [
            InlineKeyboardButton(text="🤖 AI/ML", callback_data="cat:ai"),
            InlineKeyboardButton(text="📱 Mobile", callback_data="cat:mobile"),
        ],
        [
            InlineKeyboardButton(text="☁️ DevOps", callback_data="cat:devops"),
            InlineKeyboardButton(text="🔐 Security", callback_data="cat:security"),
        ]
    ])