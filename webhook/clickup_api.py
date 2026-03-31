import requests
import os

CLICKUP_TOKEN = os.getenv("CLICKUP_API_KEY")
if not CLICKUP_TOKEN:
    raise ValueError("Missing required env var: CLICKUP_API_KEY")
TEAM_ID = os.getenv("CLICKUP_TEAM_ID")
if not TEAM_ID:
    raise ValueError("Missing required env var: CLICKUP_TEAM_ID")


def get_ngrok_url():
    try:
        response = requests.get("http://host.docker.internal:4040/api/tunnels")
        tunnels = response.json().get("tunnels", [])
        for tunnel in tunnels:
            if tunnel.get("proto") == "https":
                return tunnel["public_url"]
        print("❌ No HTTPS tunnel found.")
    except Exception as e:
        print(f"[ERROR] Could not fetch ngrok URL: {e}")
    return None


def register_webhook():
    ngrok_url = get_ngrok_url()
    if not ngrok_url:
        print("❌ Could not register webhook: ngrok not running or not found.")
        return

    webhook_url = f"{ngrok_url}/webhook"
    print(f"🔗 Registering webhook to: {webhook_url}")

    url = f"https://api.clickup.com/api/v2/team/{TEAM_ID}/webhook"
    headers = {"Authorization": CLICKUP_TOKEN, "Content-Type": "application/json"}
    payload = {"endpoint": webhook_url, "events": ["taskCreated", "taskUpdated"]}

    r = requests.post(url, json=payload, headers=headers)
    if r.ok:
        print("✅ Webhook registered successfully")
    else:
        print("❌ Webhook registration failed:", r.text)


if __name__ == "__main__":
    register_webhook()
