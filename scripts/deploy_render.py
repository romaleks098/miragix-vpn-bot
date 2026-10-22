import os
import sys
import json
import urllib.request
import urllib.error

RENDER_API_KEY = os.getenv("RENDER_API_KEY", "").strip()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

if not RENDER_API_KEY:
    print("Error: RENDER_API_KEY not found!")
    sys.exit(1)

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

print("1. Fetching Render Owner ID...")
owners_resp = make_request("https://api.render.com/v1/owners")
if isinstance(owners_resp, list) and len(owners_resp) > 0:
    owner_id = owners_resp[0]["owner"]["id"]
    print(f"Found Owner ID: {owner_id} ({owners_resp[0]['owner'].get('email', '')})")
else:
    print(f"Failed to fetch owners: {owners_resp}")
    sys.exit(1)

print("2. Checking existing services...")
services_resp = make_request("https://api.render.com/v1/services?limit=20")
existing_service = None
if isinstance(services_resp, list):
    for s in services_resp:
        srv = s.get("service", {})
        if srv.get("name") == "miragix-vpn-bot":
            existing_service = srv
            break

if existing_service:
    service_id = existing_service["id"]
    service_url = existing_service.get("serviceDetails", {}).get("url", "")
    print(f"Service already exists: {service_id}. URL: {service_url}")
    print("Triggering new deploy...")
    deploy_resp = make_request(f"https://api.render.com/v1/services/{service_id}/deploys", method="POST", data={})
    print(f"Deploy triggered: {deploy_resp}")
else:
    print("3. Creating new Web Service on Render...")
    service_payload = {
        "type": "web_service",
        "name": "miragix-vpn-bot",
        "ownerId": owner_id,
        "repo": "https://github.com/romaleks098/miragix-vpn-bot",
        "autoDeploy": "yes",
        "branch": "master",
        "serviceDetails": {
            "env": "python",
            "plan": "free",
            "region": "frankfurt",
            "buildCommand": "pip install -r requirements.txt",
            "startCommand": "python bot.py",
            "envVars": [
                {
                    "key": "BOT_TOKEN",
                    "value": BOT_TOKEN
                },
                {
                    "key": "PORT",
                    "value": "8080"
                }
            ]
        }
    }
    
    create_resp = make_request("https://api.render.com/v1/services", method="POST", data=service_payload)
    print("Create service response:", json.dumps(create_resp, indent=2))
    
    if "service" in create_resp:
        srv = create_resp["service"]
        service_id = srv.get("id")
        service_url = srv.get("serviceDetails", {}).get("url")
        print(f"\n==========================================")
        print(f"SUCCESS! Service created: {service_id}")
        print(f"Service URL: {service_url}")
        print(f"==========================================\n")
    elif "id" in create_resp:
        print(f"\n==========================================")
        print(f"SUCCESS! Service created: {create_resp['id']}")
        print(f"==========================================\n")
    else:
        print("Failed to create service:", create_resp)
        sys.exit(1)
