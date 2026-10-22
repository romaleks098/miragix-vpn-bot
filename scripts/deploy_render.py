import os
import sys
import json
import urllib.request
import time

RENDER_API_KEY = os.getenv("RENDER_API_KEY", "").strip()
SERVICE_ID = "srv-dbd7ukl9fdbs73aondsg"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json"
}

def make_request(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

print("Checking deploy and service health...")
for i in range(12):
    deploys = make_request(f"https://api.render.com/v1/services/{SERVICE_ID}/deploys?limit=1")
    if deploys:
        d = deploys[0].get("deploy", {})
        status = d.get("status")
        print(f"[{i+1}/12] Deploy {d.get('id')} status: {status}")
        if status == "live":
            print("🚀 DEPLOY IS LIVE ON RENDER!")
            # Test public URL
            try:
                with urllib.request.urlopen("https://miragix-vpn-bot.onrender.com/health", timeout=10) as h_resp:
                    print("Health check response:", h_resp.read().decode())
            except Exception as e:
                print("Health check error:", e)
            break
        elif status in ["build_failed", "update_failed", "canceled"]:
            print(f"Deploy ended with: {status}")
            break
    time.sleep(15)
