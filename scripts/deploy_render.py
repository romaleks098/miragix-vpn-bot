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

def make_request(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

deploys = make_request(f"https://api.render.com/v1/services/{SERVICE_ID}/deploys?limit=1")
if deploys:
    d = deploys[0].get("deploy", {})
    print("STATUS:", d.get("status"))
    print("ID:", d.get("id"))
