from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TARIFFS, SUPPORT_USERNAME

def main_menu_kb(has_active_sub: bool = False, trial_available: bool = True):
    buttons = []
    
    if not has_active_sub and trial_available:
        buttons.append([InlineKeyboardButton(text="🎁 Активировать тест на 3 дня", callback_data="claim_trial")])
    elif has_active_sub:
        buttons.append([InlineKeyboardButton(text="🔑 Моя подписка", callback_data="my_sub")])
        
    buttons.append([InlineKeyboardButton(text="💳 Продлить / Купить подписку", callback_data="tariffs")])
    buttons.append([InlineKeyboardButton(text="📱 Как настроить (Happ / iOS / Android)", callback_data="instructions")])
    buttons.append([InlineKeyboardButton(text="💬 Поддержка", url=f"https://t.me/{SUPPORT_USERNAME}")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def tariffs_kb():
    buttons = []
    for key, data in TARIFFS.items():
        text = f"{data['title']} — {data['price']} ₽"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"buy_{key}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def instructions_kb():
    buttons = [
        [InlineKeyboardButton(text="🍏 Инструкция для iPhone (iOS)", callback_data="inst_ios")],
        [InlineKeyboardButton(text="🤖 Инструкция для Android", callback_data="inst_android")],
        [InlineKeyboardButton(text="💻 Инструкция для Windows / ПК", callback_data="inst_pc")],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def back_to_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_main")]
    ])
