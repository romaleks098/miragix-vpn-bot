import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]

# Настройки триала (в днях)
TRIAL_DAYS = int(os.getenv("TRIAL_DAYS", "3"))

# Подключение к Marzban (если пусто, бот работает в тестовом демо-режиме)
MARZBAN_URL = os.getenv("MARZBAN_URL", "")
MARZBAN_USERNAME = os.getenv("MARZBAN_USERNAME", "")
MARZBAN_PASSWORD = os.getenv("MARZBAN_PASSWORD", "")

# Тарифы (название, дни, цена в рублях)
TARIFFS = {
    "month_1": {"title": "1 Месяц", "days": 30, "price": 150},
    "month_3": {"title": "3 Месяца", "days": 90, "price": 400},
    "month_6": {"title": "6 Месяцев", "days": 180, "price": 750},
    "year_1": {"title": "1 Год", "days": 365, "price": 1350},
}

SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "admin")
