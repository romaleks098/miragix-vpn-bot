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

srv = make_request(f"https://api.render.com/v1/services/{SERVICE_ID}")
details = srv.get("service", {}).get("serviceDetails", {})
status = srv.get("service", {}).get("status", "")
url = details.get("url", "")
print(f"Service status: {status}")
print(f"Service URL: {url}")
print(f"Build command: {details.get('buildCommand')}")
print(f"Start command: {details.get('startCommand')}")
print(f"Env: {details.get('env')}")

deploys = make_request(f"https://api.render.com/v1/services/{SERVICE_ID}/deploys?limit=1")
if deploys and len(deploys) > 0:
    d = deploys[0].get("deploy", {})
    print(f"Latest deploy status: {d.get('status')}")
    print(f"Latest deploy ID: {d.get('id')}")
