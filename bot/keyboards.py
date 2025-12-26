"""
Bot Keyboards - Inline tugmalar
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_post_keyboard(post_id: str = "0") -> InlineKeyboardMarkup:
    """Post ostidagi tugmalar"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📢 Kanalga yuborish",
                callback_data=f"publish:{post_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Qayta yozish",
                callback_data=f"regenerate:{post_id}"
            ),
            InlineKeyboardButton(
                text="✏️ Tahrirlash",
                callback_data=f"edit:{post_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Bekor qilish",
                callback_data=f"cancel:{post_id}"
            )
        ]
    ])


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Tasdiqlash tugmalari"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha", callback_data="confirm_yes"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data="confirm_no")
        ]
    ])


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Sozlamalar tugmalari"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏰ Vaqtlar", callback_data="edit_times"),
            InlineKeyboardButton(text="📝 Mavzular", callback_data="edit_topics")
        ],
        [
            InlineKeyboardButton(text="🔄 Yoqish/O'chirish", callback_data="toggle_auto")
        ]
    ])