from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import config
import database
from marzban_api import marzban_service

router = Router()

def is_admin(user_id: int) -> bool:
    return not config.ADMIN_IDS or user_id in config.ADMIN_IDS

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return

    stats = await database.get_stats()
    text = (
        "👑 <b>Панель администратора:</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"🟢 Активных подписок: <b>{stats['active_users']}</b>\n"
        f"🎁 Использовано триалов: <b>{stats['trial_users']}</b>\n\n"
        "<b>Команды управления:</b>\n"
        "• <code>/give &lt;user_id&gt; &lt;days&gt;</code> — выдать или продлить подписку пользователю вручную."
    )
    await message.answer(text, parse_mode="HTML")

@router.message(Command("give"))
async def cmd_give(message: Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Формат команды: <code>/give &lt;user_id&gt; &lt;days&gt;</code>", parse_mode="HTML")
        return

    try:
        target_id = int(parts[1])
        days = int(parts[2])
    except ValueError:
        await message.answer("Ошибка: ID пользователя и дни должны быть числами.")
        return

    result = await marzban_service.create_or_extend_user(target_id, days=days)
    if not result:
        await message.answer("❌ Ошибка при взаимодействии с сервером.")
        return

    sub_url = result["subscription_url"]
    expire_dt = await database.set_user_subscription(
        telegram_id=target_id,
        sub_url=sub_url,
        days=days
    )
    
    rewarded, ref_id = await database.reward_referrer_on_purchase(target_id)
    ref_info = ""
    if rewarded and ref_id:
        ref_info = f"\n🎁 Пригласившему пользователю <code>{ref_id}</code> начислено +{config.REFERRAL_BONUS_DAYS} дн. бонуса!"
        try:
            await message.bot.send_message(
                ref_id,
                f"🎉 <b>Бонус по реферальной программе!</b>\n\nПриглашенный вами друг оформил подписку! Вам автоматически начислено <b>+{config.REFERRAL_BONUS_DAYS} дня</b> подписки.",
                parse_mode="HTML"
            )
        except Exception:
            pass

    await message.answer(
        f"✅ Пользователю <code>{target_id}</code> успешно выдано <b>{days}</b> дней подписки (до {expire_dt.strftime('%d.%m.%Y %H:%M')}).{ref_info}",
        parse_mode="HTML"
    )
