import aiosqlite
from datetime import datetime, timedelta
import logging
import config

DB_PATH = "vpn_bot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                trial_used INTEGER DEFAULT 0,
                sub_url TEXT,
                expire_date TEXT,
                is_active INTEGER DEFAULT 0,
                referrer_id INTEGER DEFAULT 0,
                has_paid INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                tariff_key TEXT,
                amount REAL,
                status TEXT DEFAULT 'pending',
                created_at TEXT
            )
        """)
        
        await db.commit()
    logging.info("База данных инициализирована.")

async def get_user(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            return await cursor.fetchone()

async def register_user(telegram_id: int, username: str, full_name: str, referrer_id: int = 0):
    user = await get_user(telegram_id)
    if not user:
        now = datetime.now().isoformat()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO users (telegram_id, username, full_name, trial_used, is_active, referrer_id, has_paid, created_at) VALUES (?, ?, ?, 0, 0, ?, 0, ?)",
                (telegram_id, username or "", full_name or "", referrer_id or 0, now)
            )
            await db.commit()
            # Бонус за регистрацию НЕ начисляется (начисляется только после покупки!)
                
    return await get_user(telegram_id)

async def add_subscription_days(telegram_id: int, days: int):
    user = await get_user(telegram_id)
    if not user:
        return None
    now = datetime.now()
    if user["expire_date"]:
        try:
            curr_exp = datetime.fromisoformat(user["expire_date"])
            new_exp = max(curr_exp, now) + timedelta(days=days)
        except Exception:
            new_exp = now + timedelta(days=days)
    else:
        new_exp = now + timedelta(days=days)
        
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET expire_date = ?, is_active = 1 WHERE telegram_id = ?",
            (new_exp.isoformat(), telegram_id)
        )
        await db.commit()
    return new_exp

async def reward_referrer_on_purchase(buyer_id: int):
    buyer = await get_user(buyer_id)
    if not buyer:
        return False, None
        
    referrer_id = buyer["referrer_id"]
    if not referrer_id or referrer_id == buyer_id:
        return False, None

    # Проверяем, первая ли это оплата
    if not buyer["has_paid"]:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET has_paid = 1 WHERE telegram_id = ?", (buyer_id,))
            await db.commit()
            
        # Начисляем бонус пригласившему
        await add_subscription_days(referrer_id, config.REFERRAL_BONUS_DAYS)
        return True, referrer_id
        
    return False, None

async def set_user_subscription(telegram_id: int, sub_url: str, days: int, mark_trial: bool = False):
    new_expire = await add_subscription_days(telegram_id, days)
    async with aiosqlite.connect(DB_PATH) as db:
        if mark_trial:
            await db.execute(
                "UPDATE users SET sub_url = ?, trial_used = 1 WHERE telegram_id = ?",
                (sub_url, telegram_id)
            )
        else:
            await db.execute(
                "UPDATE users SET sub_url = ? WHERE telegram_id = ?",
                (sub_url, telegram_id)
            )
        await db.commit()
    return new_expire

async def get_referrals_stats(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (telegram_id,)) as cur:
            total_refs = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ? AND has_paid = 1", (telegram_id,)) as cur:
            paid_refs = (await cur.fetchone())[0]
            
        return {
            "total": total_refs,
            "paid": paid_refs,
            "earned_days": paid_refs * config.REFERRAL_BONUS_DAYS
        }

async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total_users = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_active = 1") as cur:
            active_users = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE trial_used = 1") as cur:
            trial_users = (await cur.fetchone())[0]
        return {
            "total_users": total_users,
            "active_users": active_users,
            "trial_users": trial_users
        }
