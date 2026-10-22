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

# Тарифы со сниженными ценами и скидками
TARIFFS = {
    "month_1": {
        "title": "1 Месяц",
        "days": 30,
        "price": 99,
        "old_price": 150,
        "discount": "-34%"
    },
    "month_3": {
        "title": "3 Месяца",
        "days": 90,
        "price": 249,
        "old_price": 400,
        "discount": "-38%"
    },
    "month_6": {
        "title": "6 Месяцев",
        "days": 180,
        "price": 449,
        "old_price": 750,
        "discount": "-40%"
    },
    "year_1": {
        "title": "1 Год",
        "days": 365,
        "price": 799,
        "old_price": 1350,
        "discount": "-41%"
    },
}

SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "support")
