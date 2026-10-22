import os
import sys
import json
import urllib.request

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    print("Error: BOT_TOKEN not set")
    sys.exit(1)

def call_tg(method, data):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        print(f"{method}:", res)
        return res

print("Setting Bot Description...")
call_tg("setMyDescription", {
    "description": "Добро пожаловать в Miragix VPN!\n\n🚀 Скоростной и надежный доступ к Google AI (Gemini, AI Studio), YouTube 4K и зарубежным ресурсам.\n🛡 Умная маршрутизация: российские сервисы и банки работают напрямую.\n📱 Поддержка приложения Happ на iOS, Android и Windows.\n\nНажмите Начать / Start для бесплатного теста!"
})

print("Setting Bot Short Description...")
call_tg("setMyShortDescription", {
    "short_description": "Скоростной и безопасный VPN без ограничений для Happ на iOS, Android и ПК."
})

print("Done setting descriptions!")
