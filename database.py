import aiosqlite
from datetime import datetime, timedelta
import logging

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

async def register_user(telegram_id: int, username: str, full_name: str):
    user = await get_user(telegram_id)
    if not user:
        now = datetime.now().isoformat()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO users (telegram_id, username, full_name, trial_used, is_active, created_at) VALUES (?, ?, ?, 0, 0, ?)",
                (telegram_id, username or "", full_name or "", now)
            )
            await db.commit()
    return await get_user(telegram_id)

async def set_user_subscription(telegram_id: int, sub_url: str, days: int, mark_trial: bool = False):
    user = await get_user(telegram_id)
    now = datetime.now()
    
    # Если подписка уже была активна и не истекла, продлеваем от текущего конца
    if user and user["expire_date"]:
        try:
            current_expire = datetime.fromisoformat(user["expire_date"])
            if current_expire > now:
                new_expire = current_expire + timedelta(days=days)
            else:
                new_expire = now + timedelta(days=days)
        except Exception:
            new_expire = now + timedelta(days=days)
    else:
        new_expire = now + timedelta(days=days)
        
    async with aiosqlite.connect(DB_PATH) as db:
        if mark_trial:
            await db.execute(
                "UPDATE users SET sub_url = ?, expire_date = ?, is_active = 1, trial_used = 1 WHERE telegram_id = ?",
                (sub_url, new_expire.isoformat(), telegram_id)
            )
        else:
            await db.execute(
                "UPDATE users SET sub_url = ?, expire_date = ?, is_active = 1 WHERE telegram_id = ?",
                (sub_url, new_expire.isoformat(), telegram_id)
            )
        await db.commit()
    return new_expire

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
