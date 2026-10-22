import os
import sys
import json
import urllib.request
import urllib.error

RENDER_API_KEY = os.getenv("RENDER_API_KEY", "").strip()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
SERVICE_ID = "srv-dbd7ukl9fdbs73aondsg"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def make_request(url, method="GET", data=None):
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        error_content = e.read().decode("utf-8")
        print(f"HTTP Error {e.code} on {method} {url}: {error_content}")
        return {"error": e.code, "message": error_content}
    except Exception as e:
        print(f"Request error: {e}")
        return {"error": str(e)}

print("1. Updating Environment Variables on Render...")
env_payload = [
    {"key": "BOT_TOKEN", "value": BOT_TOKEN},
    {"key": "PORT", "value": "8080"}
]
env_resp = make_request(f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars", method="PUT", data=env_payload)
print("Env vars update response:", env_resp)

print("2. Checking recent deploys...")
deploys_resp = make_request(f"https://api.render.com/v1/services/{SERVICE_ID}/deploys?limit=2")
print("Deploys:", json.dumps(deploys_resp, indent=2))
