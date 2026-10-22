from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TARIFFS, SUPPORT_USERNAME

def main_menu_kb(has_active_sub: bool = False, trial_available: bool = True):
    buttons = []
    
    # 1-й ряд: Подписка / Триал (на 24 часа)
    if not has_active_sub and trial_available:
        buttons.append([InlineKeyboardButton(text="🎁 Активировать тест на 24 часа", callback_data="claim_trial")])
    elif has_active_sub:
        buttons.append([InlineKeyboardButton(text="🔑 Моя подписка", callback_data="my_sub")])
        
    # 2-й ряд: Оплата и Центр загрузок
    buttons.append([
        InlineKeyboardButton(text="💳 Тарифы и оплата", callback_data="tariffs"),
        InlineKeyboardButton(text="📥 Скачать ПО", callback_data="downloads_center")
    ])
    
    # 3-й ряд: Инструкции и Серверы
    buttons.append([
        InlineKeyboardButton(text="📱 Инструкции", callback_data="instructions"),
        InlineKeyboardButton(text="🌐 Статус серверов", callback_data="server_status")
    ])
    
    # 4-й ряд: Реферальная программа и FAQ
    buttons.append([
        InlineKeyboardButton(text="👥 Пригласи друга (+3 дня)", callback_data="referral_program"),
        InlineKeyboardButton(text="❓ Вопросы (FAQ)", callback_data="faq_menu")
    ])
    
    # 5-й ряд: Поддержка
    buttons.append([
        InlineKeyboardButton(text="💬 Поддержка", url=f"https://t.me/{SUPPORT_USERNAME}")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def tariffs_kb():
    buttons = [
        [InlineKeyboardButton(text="🔥 1 Месяц — 99 ₽ (вместо 150 ₽)", callback_data="buy_month_1")],
        [InlineKeyboardButton(text="⚡️ 3 Месяца — 249 ₽ (вместо 400 ₽)", callback_data="buy_month_3")],
        [InlineKeyboardButton(text="💎 6 Месяцев — 449 ₽ (вместо 750 ₽)", callback_data="buy_month_6")],
        [InlineKeyboardButton(text="👑 1 Год — 799 ₽ (вместо 1350 ₽)", callback_data="buy_year_1")],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Меню Центра Загрузок ПО
def downloads_center_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🍏 iOS: Happ (App Store)", url="https://apps.apple.com/app/happ-proxy-utility/id6504287215"),
            InlineKeyboardButton(text="🍏 iOS: Streisand", url="https://apps.apple.com/app/streisand/id6450534064")
        ],
        [
            InlineKeyboardButton(text="🤖 Android: v2rayNG", url="https://play.google.com/store/apps/details?id=com.v2ray.ang"),
            InlineKeyboardButton(text="🤖 Android: Hiddify", url="https://play.google.com/store/apps/details?id=app.hiddify.com")
        ],
        [
            InlineKeyboardButton(text="💻 Windows: NekoBox", url="https://github.com/MatsuriDayo/nekoray/releases"),
            InlineKeyboardButton(text="💻 Windows: Hiddify", url="https://github.com/hiddify/hiddify-next/releases")
        ],
        [
            InlineKeyboardButton(text="🍏 Mac: FoXray", url="https://apps.apple.com/app/foxray/id6448898396"),
            InlineKeyboardButton(text="🍏 Mac: Hiddify", url="https://github.com/hiddify/hiddify-next/releases")
        ],
        [InlineKeyboardButton(text="◀️ Назад в главное меню", callback_data="back_main")]
    ])

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
        [InlineKeyboardButton(text="⚡️ Hiddify Next", callback_data="guide_pc_hiddify")],
        [InlineKeyboardButton(text="📦 Happ для Windows", callback_data="guide_pc_happ")],
        [InlineKeyboardButton(text="◀️ Назад к выбору ОС", callback_data="instructions")]
    ])

def mac_apps_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ FoXray / Streisand", callback_data="guide_mac_foxray")],
        [InlineKeyboardButton(text="⚡️ Hiddify для Mac", callback_data="guide_mac_hiddify")],
        [InlineKeyboardButton(text="◀️ Назад к выбору ОС", callback_data="instructions")]
    ])

def faq_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏦 Работают ли банки и Госуслуги?", callback_data="faq_banks")],
        [InlineKeyboardButton(text="🤖 Доступ к Google AI и ChatGPT", callback_data="faq_ai")],
        [InlineKeyboardButton(text="🛡 Как обойти шатдаун / белые списки?", callback_data="faq_shutdown")],
        [InlineKeyboardButton(text="📱 Сколько устройств можно подключить?", callback_data="faq_devices")],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_main")]
    ])

def server_status_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить статус", callback_data="server_status")],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_main")]
    ])

def back_to_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_main")]
    ])
