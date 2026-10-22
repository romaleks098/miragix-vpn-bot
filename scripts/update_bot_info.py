import os
import sys
import json
import urllib.request

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    print("Error: BOT_TOKEN not set")
    sys.exit(1)

def call_tg(method, data=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        print(f"{method}:", res)
        return res

print("Checking bot info:")
call_tg("getMe")
print("Checking bot user profile photos:")
call_tg("getUserProfilePhotos", {"user_id": 8814395665})
