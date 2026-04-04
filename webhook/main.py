from db import setup_db
from clickup_api import register_webhook
import subprocess
import sys
import time
import requests
from pathlib import Path


def wait_for_ngrok(timeout=2):
    print("⏳ Waiting for ngrok to be ready...")
    for _ in range(timeout):
        try:
            r = requests.get("http://host.docker.internal:4040/api/tunnels")
            if r.ok and "tunnels" in r.json():
                print("✅ ngrok is up!")
                return True
        except:
            pass
        time.sleep(1)
    print("❌ ngrok did not start in time.")
    return False


setup_db()

if wait_for_ngrok():
    register_webhook()
else:
    print("⚠️ Skipping webhook registration.")

_webhook_dir = Path(__file__).resolve().parent
_app = _webhook_dir / "app.py"
subprocess.run([sys.executable, str(_app)], cwd=str(_webhook_dir.parent))
