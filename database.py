import aiosqlite
from datetime import datetime, timedelta
import logging

DB_PATH = "vpn_bot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица пользователей
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
                created_at TEXT
            )
        """)
        
        # Таблица промокодов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS promocodes (
                code TEXT PRIMARY KEY,
                days INTEGER,
                max_uses INTEGER DEFAULT 100,
                used_count INTEGER DEFAULT 0
            )
        """)
        
        # Таблица активаций промокодов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS promo_activations (
                telegram_id INTEGER,
                code TEXT,
                activated_at TEXT,
                PRIMARY KEY (telegram_id, code)
            )
        """)
        
        # Таблица заказов / платежей
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
        
        # Добавляем стартовый промокод для проверки
        await db.execute("""
            INSERT OR IGNORE INTO promocodes (code, days, max_uses, used_count)
            VALUES ('MIRAGIX2026', 7, 500, 0)
        """)
        
        await db.commit()
    logging.info("База данных инициализирована с поддержкой промокодов и реферальной системы.")

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
                "INSERT INTO users (telegram_id, username, full_name, trial_used, is_active, referrer_id, created_at) VALUES (?, ?, ?, 0, 0, ?, ?)",
                (telegram_id, username or "", full_name or "", referrer_id or 0, now)
            )
            await db.commit()
            
            # Если пришел по рефералке — начисляем пригласившему бонус (+3 дня)
            if referrer_id and referrer_id != telegram_id:
                await add_subscription_days(referrer_id, days=3)
                
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

async def get_referrals_count(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (telegram_id,)) as cur:
            return (await cur.fetchone())[0]

async def activate_promocode(telegram_id: int, code: str):
    code = code.strip().upper()
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM promocodes WHERE code = ?", (code,)) as cur:
            promo = await cur.fetchone()
            
        if not promo:
            return False, "❌ Промокод не существует."
            
        if promo["used_count"] >= promo["max_uses"]:
            return False, "❌ Этот промокод уже исчерпал лимит активаций."
            
        async with db.execute("SELECT * FROM promo_activations WHERE telegram_id = ? AND code = ?", (telegram_id, code)) as cur:
            if await cur.fetchone():
                return False, "❌ Вы уже активировали этот промокод ранее."
                
        # Начисляем дни
        await add_subscription_days(telegram_id, promo["days"])
        await db.execute("INSERT INTO promo_activations VALUES (?, ?, ?)", (telegram_id, code, now))
        await db.execute("UPDATE promocodes SET used_count = used_count + 1 WHERE code = ?", (code,))
        await db.commit()
        return True, f"🎉 Промокод успешно применен! Вам начислено +{promo['days']} дней подписки."

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
