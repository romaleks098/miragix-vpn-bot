from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from datetime import datetime

import database
import keyboards
from marzban_api import marzban_service
import config

router = Router()

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
        "• Невидимость для систем блокировок (VLESS-Reality)\n"
        "• Работает через быстрое приложение <b>Happ</b> на iPhone, Android и ПК\n"
        "• Умная маршрутизация: банки и сервисы РФ работают напрямую\n\n"
        "Выберите действие в меню ниже:"
    )
    
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
    
    text = "Главное меню:"
    await call.message.edit_text(
        text,
        reply_markup=keyboards.main_menu_kb(has_active_sub=has_sub, trial_available=trial_available)
    )
    await call.answer()

@router.callback_query(F.data == "claim_trial")
async def cb_claim_trial(call: CallbackQuery):
    user = await database.get_user(call.from_user.id)
    if user and user["trial_used"]:
        await call.answer("Вы уже использовали бесплатный тестовый период!", show_alert=True)
        return

    await call.message.edit_text("⏳ Генерируем ваш персональный ключ доступа...")
    
    # Запрос к Marzban на создание пользователя
    result = await marzban_service.create_or_extend_user(call.from_user.id, days=config.TRIAL_DAYS)
    if not result:
        await call.message.edit_text(
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
        f"🔑 <b>Ваша ссылка-подписка:</b>\n"
        f"<code>{sub_url}</code>\n\n"
        "<i>(Нажмите на ссылку выше, чтобы скопировать её в буфер обмена)</i>\n\n"
        "👉 Скопируйте ссылку и добавьте её в приложение <b>Happ</b>.\n"
        "Подробную инструкцию смотрите по кнопке ниже."
    )
    
    await call.message.edit_text(
        msg_text,
        reply_markup=keyboards.instructions_kb(),
        parse_mode="HTML"
    )
    await call.answer()

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
        "<i>Вставьте эту ссылку в приложение Happ.</i>"
    )
    
    await call.message.edit_text(
        text,
        reply_markup=keyboards.back_to_menu_kb(),
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "tariffs")
async def cb_tariffs(call: CallbackQuery):
    text = (
        "💳 <b>Тарифные планы:</b>\n\n"
        "Каждый тариф включает:\n"
        "• Неограниченный скоростной трафик\n"
        "• Доступ к Google AI, YouTube, Instagram и соцсетям\n"
        "• Быстрые серверы в Европе и обход ограничений\n"
        "• Поддержку до 5 устройств на одном ключе\n\n"
        "Выберите желаемый период:"
    )
    await call.message.edit_text(text, reply_markup=keyboards.tariffs_kb(), parse_mode="HTML")
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
        "Выберите удобный способ оплаты (в разработке / подключении):\n"
        "• СБП / Банковская карта РФ\n"
        "• Telegram Stars\n"
        "• Криптовалюта (USDT / TON)\n\n"
        "<i>(Платежный шлюз подключается при запуске сервиса)</i>"
    )
    await call.message.edit_text(text, reply_markup=keyboards.back_to_menu_kb(), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "instructions")
async def cb_instructions(call: CallbackQuery):
    text = (
        "📱 <b>Инструкция по подключению:</b>\n\n"
        "Мы рекомендуем современное и быстрое приложение <b>Happ</b>.\n"
        "Выберите ваше устройство, чтобы посмотреть пошаговое руководство:"
    )
    await call.message.edit_text(text, reply_markup=keyboards.instructions_kb(), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "inst_ios")
async def cb_inst_ios(call: CallbackQuery):
    text = (
        "🍏 <b>Настройка на iPhone (iOS):</b>\n\n"
        "1. Установите приложение <b>Happ Proxy Utility</b> из App Store.\n"
        "2. Скопируйте вашу ссылку-подписку в нашем боте.\n"
        "3. Откройте Happ ➔ нажмите значок <b>«+»</b> в правом верхнем углу.\n"
        "4. Выберите <b>«Добавить из буфера обмена»</b> (Add from Clipboard).\n"
        "5. Нажмите большую кнопку включения в центре экрана.\n\n"
        "Готово! Весь заблокированный трафик и Google AI теперь работают."
    )
    await call.message.edit_text(text, reply_markup=keyboards.instructions_kb(), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "inst_android")
async def cb_inst_android(call: CallbackQuery):
    text = (
        "🤖 <b>Настройка на Android:</b>\n\n"
        "1. Установите приложение <b>Happ</b> из Google Play или APK.\n"
        "2. Скопируйте ссылку-подписку из бота.\n"
        "3. В приложении Happ нажмите <b>«+»</b> ➔ <b>«Импорт из буфера»</b>.\n"
        "4. Нажмите круглую кнопку включения.\n\n"
        "Готово! Соединение установлено."
    )
    await call.message.edit_text(text, reply_markup=keyboards.instructions_kb(), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "inst_pc")
async def cb_inst_pc(call: CallbackQuery):
    text = (
        "💻 <b>Настройка на компьютере (Windows / Mac):</b>\n\n"
        "1. Скачайте Happ для ПК или клиент <b>NekoBox / Hiddify</b>.\n"
        "2. Скопируйте ссылку-подписку из бота.\n"
        "3. Добавьте подписку в программу (Ctrl+V или Add Profile).\n"
        "4. Включите режим системного прокси (System Proxy).\n\n"
        "Готово!"
    )
    await call.message.edit_text(text, reply_markup=keyboards.instructions_kb(), parse_mode="HTML")
    await call.answer()
