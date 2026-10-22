import os
import sys
import json
import urllib.request

RENDER_API_KEY = os.getenv("RENDER_API_KEY", "").strip()
SERVICE_ID = "srv-dbd7ukl9fdbs73aondsg"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json"
}

req = urllib.request.Request(f"https://api.render.com/v1/services/{SERVICE_ID}/deploys?limit=5", headers=headers)
with urllib.request.urlopen(req) as resp:
    deploys = json.loads(resp.read().decode())
    print("Recent deploys:", json.dumps(deploys, indent=2))
