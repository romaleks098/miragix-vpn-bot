from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TARIFFS, SUPPORT_USERNAME

def main_menu_kb(has_active_sub: bool = False, trial_available: bool = True):
    buttons = []
    
    if not has_active_sub and trial_available:
        buttons.append([InlineKeyboardButton(text="🎁 Активировать тест на 3 дня", callback_data="claim_trial")])
    elif has_active_sub:
        buttons.append([InlineKeyboardButton(text="🔑 Моя подписка", callback_data="my_sub")])
        
    buttons.append([InlineKeyboardButton(text="💳 Продлить / Купить подписку", callback_data="tariffs")])
    buttons.append([InlineKeyboardButton(text="📱 Инструкции по подключению", callback_data="instructions")])
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
        [InlineKeyboardButton(text="🍏 iPhone / iPad (iOS)", callback_data="inst_ios_menu")],
        [InlineKeyboardButton(text="🤖 Android", callback_data="inst_android_menu")],
        [InlineKeyboardButton(text="💻 Windows (ПК)", callback_data="inst_pc_menu")],
        [InlineKeyboardButton(text="🍏 macOS (Mac)", callback_data="inst_mac_menu")],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def ios_apps_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ Happ Proxy (Рекомендуем)", callback_data="guide_ios_happ")],
        [InlineKeyboardButton(text="⚡️ Streisand", callback_data="guide_ios_streisand")],
        [InlineKeyboardButton(text="📦 V2Box / FoXray", callback_data="guide_ios_v2box")],
        [InlineKeyboardButton(text="◀️ Назад к выбору ОС", callback_data="instructions")]
    ])

def android_apps_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ Happ (Рекомендуем)", callback_data="guide_and_happ")],
        [InlineKeyboardButton(text="⚡️ v2rayNG", callback_data="guide_and_v2rayng")],
        [InlineKeyboardButton(text="📦 Hiddify / NekoBox", callback_data="guide_and_hiddify")],
        [InlineKeyboardButton(text="◀️ Назад к выбору ОС", callback_data="instructions")]
    ])

def pc_apps_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ NekoBox (Рекомендуем)", callback_data="guide_pc_nekobox")],
        [InlineKeyboardButton(text="⚡️ Hiddify", callback_data="guide_pc_hiddify")],
        [InlineKeyboardButton(text="📦 Happ для Windows", callback_data="guide_pc_happ")],
        [InlineKeyboardButton(text="◀️ Назад к выбору ОС", callback_data="instructions")]
    ])

def mac_apps_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ FoXray / Streisand", callback_data="guide_mac_foxray")],
        [InlineKeyboardButton(text="⚡️ Hiddify для Mac", callback_data="guide_mac_hiddify")],
        [InlineKeyboardButton(text="◀️ Назад к выбору ОС", callback_data="instructions")]
    ])

def back_to_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_main")]
    ])
