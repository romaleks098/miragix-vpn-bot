import os
import sys
import json
import urllib.request
import urllib.error

RENDER_API_KEY = os.getenv("RENDER_API_KEY", "").strip()
SERVICE_ID = "srv-dbd7ukl9fdbs73aondsg"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def make_request(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

print("--- Service details ---")
srv = make_request(f"https://api.render.com/v1/services/{SERVICE_ID}")
print(json.dumps(srv, indent=2))

print("--- Recent deploys ---")
deploys = make_request(f"https://api.render.com/v1/services/{SERVICE_ID}/deploys?limit=2")
print(json.dumps(deploys, indent=2))
