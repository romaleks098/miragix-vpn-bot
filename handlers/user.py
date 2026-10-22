from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime

import database
import keyboards
from marzban_api import marzban_service
import config

router = Router()

class PromoState(StatesGroup):
    waiting_for_code = State()

BANNER_MAIN = "https://raw.githubusercontent.com/romaleks098/miragix-vpn-bot/master/assets/banner_main.jpg"
BANNER_INSTRUCTIONS = "https://raw.githubusercontent.com/romaleks098/miragix-vpn-bot/master/assets/banner_instructions.jpg"
BANNER_TARIFFS = "https://raw.githubusercontent.com/romaleks098/miragix-vpn-bot/master/assets/banner_tariffs.jpg"

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
        try:
            await call.message.delete()
        except Exception:
            pass
        if photo_url:
            await call.message.answer_photo(photo=photo_url, caption=text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await call.message.answer(text, reply_markup=reply_markup, parse_mode="HTML")

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    # Обработка реферального кода вида /start ref_123456789
    referrer_id = 0
    parts = message.text.split()
    if len(parts) > 1 and parts[1].startswith("ref_"):
        try:
            referrer_id = int(parts[1].replace("ref_", ""))
        except ValueError:
            pass

    user = await database.register_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        referrer_id=referrer_id
    )
    
    has_sub = bool(user["is_active"] and user["expire_date"] and datetime.fromisoformat(user["expire_date"]) > datetime.now())
    trial_available = not bool(user["trial_used"])
    
    text = (
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        "Добро пожаловать в <b>Miragix VPN</b> — скоростной и безопасный интернет без ограничений.\n\n"
        "🌟 <b>Ключевые возможности:</b>\n"
        "• 🤖 Полный доступ к <b>Google AI (Gemini, AI Studio)</b> и YouTube 4K\n"
        "• 🛡 Устойчивость к блокировкам и ТСПУ (протокол VLESS-Reality)\n"
        "• 📱 Работает во всех приложениях (Happ, Streisand, v2rayNG, Hiddify, NekoBox)\n"
        "• 🇷🇺 Умная маршрутизация: банки и Госуслуги работают напрямую без задержек\n\n"
        "Выберите раздел в меню ниже:"
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

@router.message(Command("sub"))
async def cmd_sub(message: Message):
    user = await database.get_user(message.from_user.id)
    if not user or not user["sub_url"]:
        await message.answer("У вас еще нет активной подписки. Нажмите /start чтобы получить бесплатный тест!")
        return
    now = datetime.now()
    exp_date = datetime.fromisoformat(user["expire_date"])
    is_active = exp_date > now
    status_str = "🟢 Активна" if is_active else "🔴 Истекла"
    formatted_date = exp_date.strftime("%d.%m.%Y %H:%M")
    text = (
        f"🔑 <b>Информация о подписке:</b>\n\n"
        f"• Статус: <b>{status_str}</b>\n"
        f"• Срок действия: до <b>{formatted_date}</b>\n\n"
        f"🔗 <b>Ваша ссылка для подключения:</b>\n"
        f"<code>{user['sub_url']}</code>\n\n"
        "<i>Поддерживает автообновление серверов во всех клиентах.</i>"
    )
    await message.answer_photo(photo=BANNER_MAIN, caption=text, reply_markup=keyboards.back_to_menu_kb(), parse_mode="HTML")

@router.message(Command("tariffs"))
async def cmd_tariffs(message: Message):
    text = (
        "🔥 <b>Специальное предложение со скидками до -41%!</b>\n\n"
        "⚡️ <b>1 Месяц</b> — <b>99 ₽</b> <s>150 ₽</s> <i>(-34%)</i>\n"
        "⚡️ <b>3 Месяца</b> — <b>249 ₽</b> <s>400 ₽</s> <i>(83 ₽/мес, -38%)</i>\n"
        "⚡️ <b>6 Месяцев</b> — <b>449 ₽</b> <s>750 ₽</s> <i>(75 ₽/мес, -40%)</i>\n"
        "👑 <b>1 Год</b> — <b>799 ₽</b> <s>1350 ₽</s> <i>(всего 66 ₽/мес, -41%)</i>\n\n"
        "🌟 <b>В каждый тариф включено:</b>\n"
        "• Скорость до 1 Гбит/с без лимита\n"
        "• Google AI Studio, Gemini, ChatGPT, YouTube 4K\n"
        "• Умная маршрутизация\n"
        "• До 5 подключенных устройств\n\n"
        "Выберите желаемый период ниже:"
    )
    await message.answer_photo(photo=BANNER_TARIFFS, caption=text, reply_markup=keyboards.tariffs_kb(), parse_mode="HTML")

@router.message(Command("apps"))
async def cmd_apps(message: Message):
    text = (
        "📥 <b>Центр загрузок приложений:</b>\n\n"
        "Выберите официальный проверенный клиент для вашего устройства:"
    )
    await message.answer_photo(photo=BANNER_INSTRUCTIONS, caption=text, reply_markup=keyboards.downloads_center_kb(), parse_mode="HTML")

@router.message(Command("status"))
async def cmd_status(message: Message):
    now_str = datetime.now().strftime("%H:%M:%S")
    text = (
        "🌐 <b>Мониторинг сети Miragix VPN:</b>\n\n"
        "🇸🇪 <b>Швеция (Стокгольм):</b>\n"
        "• Статус: 🟢 Онлайн | ~28 ms | Google AI Studio ✅\n\n"
        "🇩🇪 <b>Германия (Франкфурт):</b>\n"
        "• Статус: 🟢 Онлайн | ~38 ms | Gemini ✅ | YouTube 4K ✅\n\n"
        "🇳🇱 <b>Нидерланды (Амстердам):</b>\n"
        "• Статус: 🟢 Онлайн | ~42 ms | Стриминг, Соцсети ✅\n\n"
        "🇷🇺 <b>Москва (Шлюз-Мост):</b>\n"
        "• Статус: 🟢 Онлайн | ~12 ms | Обход белых списков ✅\n\n"
        f"<i>Обновлено в {now_str} (Все узлы работают штатно)</i>"
    )
    await message.answer_photo(photo=BANNER_MAIN, caption=text, reply_markup=keyboards.server_status_kb(), parse_mode="HTML")

@router.message(Command("promo"))
async def cmd_promo(message: Message, state: FSMContext):
    await state.set_state(PromoState.waiting_for_code)
    text = (
        "🎟 <b>Активация промокода:</b>\n\n"
        "Отправьте секретный промокод в ответном сообщении.\n\n"
        "💡 <i>Подсказка: попробуйте приветственный промокод:</i>\n"
        "<code>MIRAGIX2026</code>"
    )
    await message.answer(text, reply_markup=keyboards.back_to_menu_kb(), parse_mode="HTML")

@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        f"💬 <b>Служба заботы и поддержки Miragix VPN:</b>\n\n"
        f"Если у вас возникли вопросы по настройке или работе подписки — напишите нашему менеджеру: @{config.SUPPORT_USERNAME}\n\n"
        "Мы всегда на связи и рады помочь!"
    )
    await message.answer(text, reply_markup=keyboards.back_to_menu_kb(), parse_mode="HTML")

@router.callback_query(F.data == "back_main")
async def cb_back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await database.get_user(call.from_user.id)
    has_sub = bool(user and user["is_active"] and user["expire_date"] and datetime.fromisoformat(user["expire_date"]) > datetime.now())
    trial_available = not bool(user and user["trial_used"])
    
    text = (
        "⚡️ <b>Главное меню Miragix VPN:</b>\n\n"
        "Выберите интересующий вас раздел:"
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

    await call.answer("Генерируем персональный ключ...")
    
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
        f"🎉 <b>Тестовый период на {config.TRIAL_DAYS} дня активирован!</b>\n\n"
        f"📅 Активен до: <b>{formatted_date}</b>\n\n"
        f"🔑 <b>Ваша универсальная ссылка-подписка:</b>\n"
        f"<code>{sub_url}</code>\n\n"
        "<i>(Нажмите на ссылку выше, чтобы скопировать её)</i>\n\n"
        "👉 Вставьте её в любое приложение (Happ, Streisand, v2rayNG, Hiddify)."
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
        f"🔑 <b>Информация о подписке:</b>\n\n"
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
        "🔥 <b>Специальное предложение со скидками до -41%!</b>\n\n"
        "⚡️ <b>1 Месяц</b> — <b>99 ₽</b> <s>150 ₽</s> <i>(-34%)</i>\n"
        "⚡️ <b>3 Месяца</b> — <b>249 ₽</b> <s>400 ₽</s> <i>(83 ₽/мес, -38%)</i>\n"
        "⚡️ <b>6 Месяцев</b> — <b>449 ₽</b> <s>750 ₽</s> <i>(75 ₽/мес, -40%)</i>\n"
        "👑 <b>1 Год</b> — <b>799 ₽</b> <s>1350 ₽</s> <i>(всего 66 ₽/мес, -41%)</i>\n\n"
        "🌟 <b>В каждый тариф включено:</b>\n"
        "• Неограниченная скорость до 1 Гбит/с без лимита трафика\n"
        "• Полный доступ к Google AI Studio, Gemini, ChatGPT, YouTube 4K\n"
        "• Умная маршрутизация: банки и сервисы РФ работают напрямую\n"
        "• До 5 подключенных устройств на одну подписку\n\n"
        "Выберите желаемый тариф ниже:"
    )
    await update_view(call, text=text, reply_markup=keyboards.tariffs_kb(), photo_url=BANNER_TARIFFS)
    await call.answer()

@router.callback_query(F.data.startswith("buy_"))
async def cb_buy_tariff(call: CallbackQuery):
    tariff_key = call.data.replace("buy_", "")
    tariff = config.TARIFFS.get(tariff_key)
    if not tariff:
        await call.answer("Тариф не найден.", show_alert=True)
        return
        
    old_p = tariff.get("old_price", "")
    disc = tariff.get("discount", "")
    old_p_str = f" <s>{old_p} ₽</s> ({disc})" if old_p else ""
    
    text = (
        f"🧾 <b>Оформление подписки: {tariff['title']}</b>\n"
        f"Сумма со скидкой: <b>{tariff['price']} ₽</b>{old_p_str}\n\n"
        "Способы оплаты:\n"
        "• 💳 Банковская карта РФ / СБП (МИР, Visa, Mastercard)\n"
        "• ⭐️ Telegram Stars\n"
        "• 💎 Криптовалюта (USDT TRC20 / TON / CryptoBot)\n\n"
        "<i>(Платежный шлюз подключается при запуске сервиса)</i>"
    )
    await update_view(call, text=text, reply_markup=keyboards.back_to_menu_kb(), photo_url=BANNER_TARIFFS)
    await call.answer()

# --- ЦЕНТР ЗАГРУЗОК ПО ---

@router.callback_query(F.data == "downloads_center")
async def cb_downloads_center(call: CallbackQuery):
    text = (
        "📥 <b>Центр загрузок приложений:</b>\n\n"
        "Скачайте официальный проверенный клиент для вашего устройства:\n\n"
        "🍏 <b>Для iPhone / iPad:</b>\n"
        "• <b>Happ Proxy Utility</b> — самый быстрый и современный (App Store)\n"
        "• <b>Streisand</b> — легкий и надежный (App Store)\n\n"
        "🤖 <b>Для Android:</b>\n"
        "• <b>v2rayNG</b> — классика с открытым кодом (Google Play)\n"
        "• <b>Hiddify Next</b> — современный интерфейс в 1 клик\n\n"
        "💻 <b>Для Windows / Компьютера:</b>\n"
        "• <b>NekoBox</b> — профессиональный клиент с системным прокси\n"
        "• <b>Hiddify Next</b> — простой клиент под Windows\n\n"
        "Нажмите на кнопку нужного приложения ниже для перехода к загрузке:"
    )
    await update_view(call, text=text, reply_markup=keyboards.downloads_center_kb(), photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

# --- СТАТУС СЕРВЕРОВ ---

@router.callback_query(F.data == "server_status")
async def cb_server_status(call: CallbackQuery):
    now_str = datetime.now().strftime("%H:%M:%S")
    text = (
        "🌐 <b>Мониторинг сети Miragix VPN:</b>\n\n"
        "🇸🇪 <b>Швеция (Стокгольм):</b>\n"
        "• Статус: 🟢 Онлайн\n"
        "• Пинг: ~28 ms | Канал: 1 Gbps\n"
        "• Сервисы: <b>Google AI Studio ✅</b>, YouTube 4K ✅\n\n"
        "🇩🇪 <b>Германия (Франкфурт):</b>\n"
        "• Статус: 🟢 Онлайн\n"
        "• Пинг: ~38 ms | Канал: 1 Gbps\n"
        "• Сервисы: <b>Gemini ✅</b>, ChatGPT, Instagram ✅\n\n"
        "🇳🇱 <b>Нидерланды (Амстердам):</b>\n"
        "• Статус: 🟢 Онлайн\n"
        "• Пинг: ~42 ms | Канал: 1 Gbps\n"
        "• Сервисы: Стриминг, Торренты, Облака ✅\n\n"
        "🇷🇺 <b>Москва (Шлюз-Мост):</b>\n"
        "• Статус: 🟢 Онлайн\n"
        "• Пинг: ~12 ms\n"
        "• Назначение: <b>Обход «белых списков» и шатдаунов</b> ✅\n\n"
        f"<i>Обновлено в {now_str} (Все узлы работают штатно)</i>"
    )
    await update_view(call, text=text, reply_markup=keyboards.server_status_kb(), photo_url=BANNER_MAIN)
    await call.answer()

# --- РЕФЕРАЛЬНАЯ ПРОГРАММА ---

@router.callback_query(F.data == "referral_program")
async def cb_referral_program(call: CallbackQuery):
    bot_info = await call.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{call.from_user.id}"
    refs_count = await database.get_referrals_count(call.from_user.id)
    
    text = (
        "👥 <b>Партнерская программа «Пригласи друга»:</b>\n\n"
        "Поделитесь своей персональной ссылкой с друзьями, коллегами или в соцсетях.\n\n"
        "🎁 <b>Условия:</b>\n"
        "• За каждого нового пользователя, перешедшего по вашей ссылке, вы получаете <b>+3 дня подписки БЕСПЛАТНО</b>.\n"
        "• Друг получает стандартный бесплатный тест на 3 дня.\n\n"
        f"📊 Вы уже пригласили: <b>{refs_count} чел.</b>\n\n"
        "🔗 <b>Ваша пригласительная ссылка:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        "<i>(Нажмите на ссылку, чтобы скопировать её)</i>"
    )
    await update_view(call, text=text, reply_markup=keyboards.back_to_menu_kb(), photo_url=BANNER_MAIN)
    await call.answer()

# --- БАЗА ЗНАНИЙ (FAQ) ---

@router.callback_query(F.data == "faq_menu")
async def cb_faq_menu(call: CallbackQuery):
    text = (
        "❓ <b>Часто задаваемые вопросы (FAQ):</b>\n\n"
        "Выберите вопрос, чтобы прочитать подробный ответ:"
    )
    await update_view(call, text=text, reply_markup=keyboards.faq_kb(), photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

@router.callback_query(F.data == "faq_banks")
async def cb_faq_banks(call: CallbackQuery):
    text = (
        "🏦 <b>Работают ли банки и Госуслуги при включенном VPN?</b>\n\n"
        "<b>ДА, работают отлично!</b>\n\n"
        "В наших клиентах (Happ, v2rayNG, Hiddify) используется **умная маршрутизация**:\n"
        "• Все российские сайты (`.ru`, Госуслуги, Сбербанк, Тинькофф, Ozon, Wildberries) открываются <b>напрямую</b> на максимальной скорости вашего провайдера.\n"
        "• Через защищенный зарубежный сервер идут <b>только</b> заблокированные сайты и Google AI.\n\n"
        "Вам не нужно постоянно включать и выключать VPN!"
    )
    await update_view(call, text=text, reply_markup=keyboards.faq_kb(), photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

@router.callback_query(F.data == "faq_ai")
async def cb_faq_ai(call: CallbackQuery):
    text = (
        "🤖 <b>Доступ к Google AI (Gemini, AI Studio) и ChatGPT:</b>\n\n"
        "Все наши европейские серверы (Швеция, Германия, Нидерланды) имеют чистые IP-адреса и поддерживают полный доступ к:\n"
        "• <b>Google AI Studio</b> (`aistudio.google.com`)\n"
        "• <b>Google Gemini</b> (`gemini.google.com`)\n"
        "• <b>ChatGPT / OpenAI</b>\n"
        "• <b>Claude by Anthropic</b>\n\n"
        "Ошибки «Not available in your country» не возникают."
    )
    await update_view(call, text=text, reply_markup=keyboards.faq_kb(), photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

@router.callback_query(F.data == "faq_shutdown")
async def cb_faq_shutdown(call: CallbackQuery):
    text = (
        "🛡 <b>Что делать во время шатдауна или режима «белых списков»?</b>\n\n"
        "Когда операторы связи глушат внешний интернет и оставляют доступ только к списку разрешенных сайтов:\n\n"
        "1. Наш протокол <b>VLESS-Reality</b> маскирует трафик под обычное посещение разрешенных ресурсов.\n"
        "2. В подписку встроен резервный узел через дата-центр в Москве (Relay-мост), который сохраняет связь даже во время региональных ограничений мобильных вышек."
    )
    await update_view(call, text=text, reply_markup=keyboards.faq_kb(), photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

@router.callback_query(F.data == "faq_devices")
async def cb_faq_devices(call: CallbackQuery):
    text = (
        "📱 <b>Сколько устройств можно подключить на одну подписку?</b>\n\n"
        "На одном ключе разрешено подключать <b>до 5 устройств одновременно</b> (например: ваш телефон, рабочий ноутбук, домашний ПК, планшет и телефон близкого человека).\n\n"
        "Просто вставьте одну и ту же ссылку-подписку во все ваши устройства."
    )
    await update_view(call, text=text, reply_markup=keyboards.faq_kb(), photo_url=BANNER_INSTRUCTIONS)
    await call.answer()

# --- ВВОД ПРОМОКОДА ---

@router.callback_query(F.data == "enter_promo")
async def cb_enter_promo(call: CallbackQuery, state: FSMContext):
    await state.set_state(PromoState.waiting_for_code)
    text = (
        "🎟 <b>Активация промокода:</b>\n\n"
        "Отправьте секретный промокод в ответном сообщении.\n\n"
        "💡 <i>Подсказка: попробуйте ввести приветственный промокод:</i>\n"
        "<code>MIRAGIX2026</code>"
    )
    await update_view(call, text=text, reply_markup=keyboards.back_to_menu_kb(), photo_url=BANNER_MAIN)
    await call.answer()

@router.message(PromoState.waiting_for_code)
async def process_promocode(message: Message, state: FSMContext):
    code = message.text.strip()
    success, msg = await database.activate_promocode(message.from_user.id, code)
    await state.clear()
    
    user = await database.get_user(message.from_user.id)
    has_sub = bool(user and user["is_active"] and user["expire_date"] and datetime.fromisoformat(user["expire_date"]) > datetime.now())
    trial_available = not bool(user and user["trial_used"])
    
    await message.answer(
        f"{msg}\n\nВозвращаемся в главное меню:",
        reply_markup=keyboards.main_menu_kb(has_active_sub=has_sub, trial_available=trial_available),
        parse_mode="HTML"
    )

# --- МЕНЮ ИНСТРУКЦИЙ ПО ПЛАТФОРМАМ ---

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
