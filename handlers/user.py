from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.filters import CommandStart
from datetime import datetime
import os

import database
import keyboards
from marzban_api import marzban_service
import config

router = Router()

BANNER_MAIN = "https://raw.githubusercontent.com/romaleks098/miragix-vpn-bot/master/assets/banner_main.jpg"
BANNER_INSTRUCTIONS = "https://raw.githubusercontent.com/romaleks098/miragix-vpn-bot/master/assets/banner_instructions.jpg"

async def update_view(call: CallbackQuery, text: str, reply_markup=None, photo_url: str = None):
    try:
        if photo_url:
            media = InputMediaPhoto(media=photo_url, caption=text, parse_mode="HTML")
            await call.message.edit_media(media=media, reply_markup=reply_markup)
        elif call.message.photo:
            await call.message.edit_caption(caption=text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await call.message.edit_text(text=text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception:
        # Если не удалось отредактировать (например, переход между разными типами сообщений)
        try:
            await call.message.delete()
        except Exception:
            pass
        if photo_url:
            await call.message.answer_photo(photo=photo_url, caption=text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await call.message.answer(text, reply_markup=reply_markup, parse_mode="HTML")

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await database.register_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )
    
    has_sub = bool(user["is_active"] and user["expire_date"] and datetime.fromisoformat(user["expire_date"]) > datetime.now())
    trial_available = not bool(user["trial_used"])
    
    text = (
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        "Добро пожаловать в <b>Miragix VPN</b> — скоростной и безопасный интернет без ограничений.\n\n"
        "🌟 <b>Наши преимущества:</b>\n"
        "• Полный доступ к <b>Google AI (Gemini, AI Studio)</b> и YouTube в 4K\n"
        "• Невидимость для систем блокировок (протоколы VLESS-Reality)\n"
        "• Универсальная подписка: работает в <b>Happ, Streisand, v2rayNG, Hiddify, NekoBox</b>\n"
        "• Умная маршрутизация: банки и сервисы РФ работают напрямую\n\n"
        "Выберите действие в меню ниже:"
    )
    
    try:
        await message.answer_photo(
            photo=BANNER_MAIN,
            caption=text,
            reply_markup=keyboards.main_menu_kb(has_active_sub=has_sub, trial_available=trial_available),
            parse_mode="HTML"
        )
    except Exception:
        await message.answer(
            text,
            reply_markup=keyboards.main_menu_kb(has_active_sub=has_sub, trial_available=trial_available),
            parse_mode="HTML"
        )

@router.callback_query(F.data == "back_main")
async def cb_back_main(call: CallbackQuery):
    user = await database.get_user(call.from_user.id)
    has_sub = bool(user and user["is_active"] and user["expire_date"] and datetime.fromisoformat(user["expire_date"]) > datetime.now())
    trial_available = not bool(user and user["trial_used"])
    
    text = (
        "⚡️ <b>Главное меню Miragix VPN:</b>\n\n"
        "Выберите нужный раздел ниже:"
    )
    await update_view(
        call,
        text=text,
        reply_markup=keyboards.main_menu_kb(has_active_sub=has_sub, trial_available=trial_available),
        photo_url=BANNER_MAIN
    )
    await call.answer()

@router.callback_query(F.data == "claim_trial")
async def cb_claim_trial(call: CallbackQuery):
    user = await database.get_user(call.from_user.id)
    if user and user["trial_used"]:
        await call.answer("Вы уже использовали бесплатный тестовый период!", show_alert=True)
        return

    await call.answer("Генерируем ваш ключ доступа...")
    
    result = await marzban_service.create_or_extend_user(call.from_user.id, days=config.TRIAL_DAYS)
    if not result:
        await update_view(
            call,
            "❌ Не удалось выдать подписку. Обратитесь в поддержку.",
            reply_markup=keyboards.back_to_menu_kb()
        )
        return
        
    sub_url = result["subscription_url"]
    expire_dt = await database.set_user_subscription(
        telegram_id=call.from_user.id,
        sub_url=sub_url,
        days=config.TRIAL_DAYS,
        mark_trial=True
    )
    
    formatted_date = expire_dt.strftime("%d.%m.%Y %H:%M")
    
    msg_text = (
        f"🎉 <b>Тестовый период на {config.TRIAL_DAYS} дня успешно активирован!</b>\n\n"
        f"📅 Активен до: <b>{formatted_date}</b>\n\n"
        f"🔑 <b>Ваша универсальная ссылка-подписка:</b>\n"
        f"<code>{sub_url}</code>\n\n"
        "<i>(Нажмите на ссылку выше, чтобы скопировать её в буфер обмена)</i>\n\n"
        "👉 Скопируйте ссылку и добавьте её в любое приложение (Happ, Streisand, v2rayNG, Hiddify)."
    )
    
    await update_view(
        call,
        text=msg_text,
        reply_markup=keyboards.instructions_kb(),
        photo_url=BANNER_INSTRUCTIONS
    )

@router.callback_query(F.data == "my_sub")
async def cb_my_sub(call: CallbackQuery):
    user = await database.get_user(call.from_user.id)
    if not user or not user["sub_url"]:
        await call.answer("У вас еще нет активной подписки.", show_alert=True)
        return
        
    now = datetime.now()
    exp_date = datetime.fromisoformat(user["expire_date"])
    is_active = exp_date > now
    
    status_str = "🟢 Активна" if is_active else "🔴 Истекла"
    formatted_date = exp_date.strftime("%d.%m.%Y %H:%M")
    
    text = (
        f"🔑 <b>Информация о вашей подписке:</b>\n\n"
        f"• Статус: <b>{status_str}</b>\n"
        f"• Срок действия: до <b>{formatted_date}</b>\n\n"
        f"🔗 <b>Ваша ссылка для подключения:</b>\n"
        f"<code>{user['sub_url']}</code>\n\n"
        "<i>Поддерживает автообновление серверов во всех клиентах.</i>"
    )
    
    await update_view(call, text=text, reply_markup=keyboards.back_to_menu_kb(), photo_url=BANNER_MAIN)
    await call.answer()

@router.callback_query(F.data == "tariffs")
async def cb_tariffs(call: CallbackQuery):
    text = (
        "💳 <b>Тарифные планы Miragix VPN:</b>\n\n"
        "Все тарифы включают:\n"
        "• Неограниченную скорость и трафик\n"
        "• Доступ к Google AI, YouTube 4K, ChatGPT, Instagram\n"
        "• Защиту от систем блокировок\n"
        "• До 5 устройств на одном ключе\n\n"
        "Выберите желаемый период:"
    )
    await update_view(call, text=text, reply_markup=keyboards.tariffs_kb(), photo_url=BANNER_MAIN)
    await call.answer()

@router.callback_query(F.data.startswith("buy_"))
async def cb_buy_tariff(call: CallbackQuery):
    tariff_key = call.data.replace("buy_", "")
    tariff = config.TARIFFS.get(tariff_key)
    if not tariff:
        await call.answer("Тариф не найден.", show_alert=True)
        return
        
    text = (
        f"🧾 <b>Оформление подписки: {tariff['title']}</b>\n"
        f"Сумма к оплате: <b>{tariff['price']} ₽</b>\n\n"
        "Способы оплаты:\n"
        "• СБП / Банковская карта РФ (МИР, Visa, Mastercard)\n"
        "• Telegram Stars (Звезды)\n"
        "• Криптовалюта (USDT TRC20 / TON)\n\n"
        "<i>(Платежный шлюз подключается при переходе на боевой сервер)</i>"
    )
    await update_view(call, text=text, reply_markup=keyboards.back_to_menu_kb(), photo_url=BANNER_MAIN)
    await call.answer()

# --- МЕНЮ ИНСТРУКЦИЙ С БАННЕРАМИ ---

@router.callback_query(F.data == "instructions")
async def cb_instructions(call: CallbackQuery):
    text = (
        "📱 <b>Инструкции по настройке VPN:</b>\n\n"
        "Наша подписка универсальна и работает во всех приложениях на любом устройстве.\n\n"
        "Выберите вашу операционную систему:"
    )
    await update_view(call, text=text, reply_markup=keyboards.instructions_kb(), photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

@router.callback_query(F.data == "inst_ios_menu")
async def cb_inst_ios_menu(call: CallbackQuery):
    text = "🍏 <b>Выберите приложение для iPhone / iPad:</b>"
    await update_view(call, text=text, reply_markup=keyboards.ios_apps_kb(), photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

@router.callback_query(F.data == "inst_android_menu")
async def cb_inst_android_menu(call: CallbackQuery):
    text = "🤖 <b>Выберите приложение для Android:</b>"
    await update_view(call, text=text, reply_markup=keyboards.android_apps_kb(), photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

@router.callback_query(F.data == "inst_pc_menu")
async def cb_inst_pc_menu(call: CallbackQuery):
    text = "💻 <b>Выберите приложение для Windows (ПК):</b>"
    await update_view(call, text=text, reply_markup=keyboards.pc_apps_kb(), photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

@router.callback_query(F.data == "inst_mac_menu")
async def cb_inst_mac_menu(call: CallbackQuery):
    text = "🍏 <b>Выберите приложение для macOS (Mac):</b>"
    await update_view(call, text=text, reply_markup=keyboards.mac_apps_kb(), photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

# --- ПОШАГОВЫЕ ГАЙДЫ ---

@router.callback_query(F.data == "guide_ios_happ")
async def cb_guide_ios_happ(call: CallbackQuery):
    text = (
        "⭐️ <b>Настройка Happ на iPhone (iOS):</b>\n\n"
        "1. Установите <a href='https://apps.apple.com/app/happ-proxy-utility/id6504287215'>Happ Proxy Utility</a> из App Store.\n"
        "2. Скопируйте ссылку-подписку в разделе «Моя подписка».\n"
        "3. Откройте Happ ➔ нажмите <b>«+»</b> вверху справа.\n"
        "4. Выберите <b>«Добавить из буфера»</b> (Add from Clipboard).\n"
        "5. Нажмите круглую кнопку подключения в центре.\n\n"
        "💡 <i>В настройках включите «Rule mode», чтобы российские банки и сайты работали без VPN.</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать Happ в App Store", url="https://apps.apple.com/app/happ-proxy-utility/id6504287215")],
        [InlineKeyboardButton(text="◀️ Назад к приложениям iOS", callback_data="inst_ios_menu")]
    ])
    await update_view(call, text=text, reply_markup=kb, photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

@router.callback_query(F.data == "guide_ios_streisand")
async def cb_guide_ios_streisand(call: CallbackQuery):
    text = (
        "⚡️ <b>Настройка Streisand на iPhone (iOS):</b>\n\n"
        "1. Установите <a href='https://apps.apple.com/app/streisand/id6450534064'>Streisand</a> из App Store.\n"
        "2. Скопируйте вашу ссылку-подписку в боте.\n"
        "3. Откройте Streisand ➔ нажмите значок <b>«+»</b> в правом верхнем углу.\n"
        "4. Выберите «Import from Clipboard».\n"
        "5. Нажмите кнопку подключения."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать Streisand в App Store", url="https://apps.apple.com/app/streisand/id6450534064")],
        [InlineKeyboardButton(text="◀️ Назад к приложениям iOS", callback_data="inst_ios_menu")]
    ])
    await update_view(call, text=text, reply_markup=kb, photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

@router.callback_query(F.data == "guide_ios_v2box")
async def cb_guide_ios_v2box(call: CallbackQuery):
    text = (
        "📦 <b>Настройка V2Box / FoXray на iPhone:</b>\n\n"
        "1. Установите <a href='https://apps.apple.com/app/v2box-v2ray-client/id6446814690'>V2Box</a> или <a href='https://apps.apple.com/app/foxray/id6448898396'>FoXray</a> из App Store.\n"
        "2. Скопируйте ссылку-подписку в боте.\n"
        "3. В приложении перейдите в <b>Configs</b> ➔ нажмите <b>«+»</b>.\n"
        "4. Выберите <b>«Add Subscription»</b> и вставьте ссылку.\n"
        "5. Обновите подписку и включите тумблер."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать V2Box", url="https://apps.apple.com/app/v2box-v2ray-client/id6446814690")],
        [InlineKeyboardButton(text="📥 Скачать FoXray", url="https://apps.apple.com/app/foxray/id6448898396")],
        [InlineKeyboardButton(text="◀️ Назад к приложениям iOS", callback_data="inst_ios_menu")]
    ])
    await update_view(call, text=text, reply_markup=kb, photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

@router.callback_query(F.data == "guide_and_happ")
async def cb_guide_and_happ(call: CallbackQuery):
    text = (
        "⭐️ <b>Настройка Happ на Android:</b>\n\n"
        "1. Установите приложение <b>Happ</b>.\n"
        "2. Скопируйте вашу ссылку-подписку в боте.\n"
        "3. В приложении нажмите <b>«+»</b> ➔ <b>«Импорт из буфера обмена»</b>.\n"
        "4. Нажмите круглую кнопку подключения."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к приложениям Android", callback_data="inst_android_menu")]
    ])
    await update_view(call, text=text, reply_markup=kb, photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

@router.callback_query(F.data == "guide_and_v2rayng")
async def cb_guide_and_v2rayng(call: CallbackQuery):
    text = (
        "⚡️ <b>Настройка v2rayNG на Android:</b>\n\n"
        "1. Установите <a href='https://play.google.com/store/apps/details?id=com.v2ray.ang'>v2rayNG</a> из Google Play.\n"
        "2. Скопируйте вашу ссылку-подписку в боте.\n"
        "3. В боковом меню ➔ <b>Группы подписок</b> ➔ нажмите <b>«+»</b>.\n"
        "4. Вставьте ссылку и сохраните.\n"
        "5. На главном экране: 3 точки ➔ <b>Обновить подписку</b> ➔ подключитесь."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать v2rayNG", url="https://play.google.com/store/apps/details?id=com.v2ray.ang")],
        [InlineKeyboardButton(text="◀️ Назад к приложениям Android", callback_data="inst_android_menu")]
    ])
    await update_view(call, text=text, reply_markup=kb, photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

@router.callback_query(F.data == "guide_and_hiddify")
async def cb_guide_and_hiddify(call: CallbackQuery):
    text = (
        "📦 <b>Настройка Hiddify / NekoBox на Android:</b>\n\n"
        "1. Установите <a href='https://play.google.com/store/apps/details?id=app.hiddify.com'>Hiddify Next</a> из Google Play.\n"
        "2. Скопируйте ссылку-подписку в боте.\n"
        "3. В Hiddify нажмите <b>«Новый профиль»</b> ➔ <b>«Добавить из буфера»</b>.\n"
        "4. Нажмите большую кнопку подключения."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать Hiddify", url="https://play.google.com/store/apps/details?id=app.hiddify.com")],
        [InlineKeyboardButton(text="◀️ Назад к приложениям Android", callback_data="inst_android_menu")]
    ])
    await update_view(call, text=text, reply_markup=kb, photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

@router.callback_query(F.data == "guide_pc_nekobox")
async def cb_guide_pc_nekobox(call: CallbackQuery):
    text = (
        "⭐️ <b>Настройка NekoBox на Windows (ПК):</b>\n\n"
        "1. Скачайте <b>NekoBox for Windows</b> с GitHub.\n"
        "2. Запустите `nekobox.exe`.\n"
        "3. Нажмите `Ctrl + V` в окне программы.\n"
        "4. Включите галочку <b>«Режим системного прокси»</b> (System Proxy)."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать NekoBox для Windows", url="https://github.com/MatsuriDayo/nekoray/releases")],
        [InlineKeyboardButton(text="◀️ Назад к приложениям ПК", callback_data="inst_pc_menu")]
    ])
    await update_view(call, text=text, reply_markup=kb, photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

@router.callback_query(F.data == "guide_pc_hiddify")
async def cb_guide_pc_hiddify(call: CallbackQuery):
    text = (
        "⚡️ <b>Настройка Hiddify на Windows:</b>\n\n"
        "1. Скачайте <b>Hiddify Next</b> для Windows.\n"
        "2. Нажмите «+» ➔ добавьте ссылку из буфера.\n"
        "3. Включите тумблер VPN."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать Hiddify для Windows", url="https://github.com/hiddify/hiddify-next/releases")],
        [InlineKeyboardButton(text="◀️ Назад к приложениям ПК", callback_data="inst_pc_menu")]
    ])
    await update_view(call, text=text, reply_markup=kb, photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

@router.callback_query(F.data == "guide_pc_happ")
async def cb_guide_pc_happ(call: CallbackQuery):
    text = (
        "📦 <b>Настройка Happ для Windows:</b>\n\n"
        "1. Скачайте Happ Client для Windows.\n"
        "2. Вставьте скопированную ссылку через «+».\n"
        "3. Нажмите кнопку подключения."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к приложениям ПК", callback_data="inst_pc_menu")]
    ])
    await update_view(call, text=text, reply_markup=kb, photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

@router.callback_query(F.data == "guide_mac_foxray")
async def cb_guide_mac_foxray(call: CallbackQuery):
    text = (
        "🍏 <b>Настройка на macOS (Mac):</b>\n\n"
        "1. Установите <b>FoXray</b> или <b>Streisand</b> из Mac App Store.\n"
        "2. Скопируйте ссылку в боте ➔ вставьте через «+».\n"
        "3. Нажмите кнопку Connect."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать FoXray в Mac App Store", url="https://apps.apple.com/app/foxray/id6448898396")],
        [InlineKeyboardButton(text="◀️ Назад к приложениям Mac", callback_data="inst_mac_menu")]
    ])
    await update_view(call, text=text, reply_markup=kb, photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

@router.callback_query(F.data == "guide_mac_hiddify")
async def cb_guide_mac_hiddify(call: CallbackQuery):
    text = (
        "⚡️ <b>Настройка Hiddify на macOS:</b>\n\n"
        "1. Установите <b>Hiddify Next</b> для macOS.\n"
        "2. Скопируйте вашу ссылку в боте.\n"
        "3. Нажмите «Добавить из буфера» ➔ включите VPN."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать Hiddify для Mac", url="https://github.com/hiddify/hiddify-next/releases")],
        [InlineKeyboardButton(text="◀️ Назад к приложениям Mac", callback_data="inst_mac_menu")]
    ])
    await update_view(call, text=text, reply_markup=kb, photo_url=BANNER_INSTRUCTIONS)
    await call.answer()
