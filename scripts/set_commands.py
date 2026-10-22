import os
import sys
import json
import urllib.request

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    sys.exit(1)

def call_tg(method, data):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        print(f"{method}:", res)
        return res

commands = [
    {"command": "start", "description": "⚡️ Главное меню"},
    {"command": "sub", "description": "🔑 Моя подписка"},
    {"command": "tariffs", "description": "💳 Тарифы и акции"},
    {"command": "apps", "description": "📥 Скачать приложения"},
    {"command": "status", "description": "🌐 Мониторинг серверов"},
    {"command": "promo", "description": "🎟 Ввести промокод"},
    {"command": "help", "description": "💬 Помощь и поддержка"}
]

print("Setting Bot Commands...")
call_tg("setMyCommands", {"commands": commands})
