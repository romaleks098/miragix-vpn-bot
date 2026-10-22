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

for i in range(5):
    deploys = make_request(f"https://api.render.com/v1/services/{SERVICE_ID}/deploys?limit=1")
    if deploys and len(deploys) > 0:
        d = deploys[0].get("deploy", {})
        status = d.get("status")
        print(f"[{i+1}/5] Deploy {d.get('id')} status: {status}")
        if status in ["live", "build_failed", "update_failed", "canceled"]:
            break
    time.sleep(10)
