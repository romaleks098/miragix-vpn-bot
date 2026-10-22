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

req = urllib.request.Request(f"https://api.render.com/v1/services/{SERVICE_ID}", headers=headers)
with urllib.request.urlopen(req) as resp:
    srv = json.loads(resp.read().decode())
    print("Service details:", json.dumps(srv, indent=2))
