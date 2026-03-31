from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

CLICKUP_TOKEN = os.getenv("CLICKUP_API_KEY")
if not CLICKUP_TOKEN:
    raise ValueError("Missing required env var: CLICKUP_API_KEY")


def get_task_details(task_id):
    url = f"https://api.clickup.com/api/v2/task/{task_id}"
    headers = {"Authorization": CLICKUP_TOKEN, "Content-Type": "application/json"}
    try:
        r = requests.get(url, headers=headers)
        if r.ok:
            return r.json()
        else:
            print(f"[ERROR] Failed to fetch task details: {r.status_code} {r.text}")
            return None
    except Exception as e:
        print(f"[ERROR] Exception during get_task_details: {e}")
        return None


def add_time_tracked(task_id, start_ms, end_ms):
    url = f"https://api.clickup.com/api/v2/task/{task_id}/time"
    headers = {"Authorization": CLICKUP_TOKEN, "Content-Type": "application/json"}
    duration_ms = end_ms - start_ms
    payload = {
        "start": start_ms,
        "end": end_ms,
        "duration": duration_ms,
        "billable": True,
        "description": "Auto time tracked based on start and due date difference",
    }
    try:
        r = requests.post(url, json=payload, headers=headers)
        if r.ok:
            print(f"[INFO] Added time tracked to task {task_id}")
            return True
        else:
            print(f"[ERROR] Failed to add time tracked: {r.status_code} {r.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Exception during add_time_tracked: {e}")
        return False


@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    print(f"[INFO] Received {request.method} request at /webhook")

    if request.method == "GET":
        challenge = request.args.get("challenge")
        print(f"[INFO] GET challenge: {challenge}")
        if challenge:
            return jsonify({"challenge": challenge})

    try:
        data = request.get_json(force=True)
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON: {e}")
        return jsonify({"error": "Invalid JSON"}), 400

    print(f"[INFO] Received webhook data: {data}")

    try:
        if data.get("event") == "taskCreated":
            task_id = data.get("task_id")
            if not task_id:
                print("[WARNING] No task_id found in webhook data.")
                return jsonify({"status": "no task_id"}), 400

            # Fetch full task details from ClickUp API
            task_details = get_task_details(task_id)
            if not task_details:
                return jsonify({"status": "failed to fetch task details"}), 500

            start_date = task_details.get("start_date")
            due_date = task_details.get("due_date")

            if start_date is None or due_date is None:
                print(
                    f"[WARNING] Task {task_id} missing start_date or due_date in task details."
                )
                return jsonify({"status": "missing dates"}), 200

            try:
                start_date = int(start_date)
                due_date = int(due_date)
            except ValueError as e:
                print(f"[ERROR] Invalid date format in task {task_id}: {e}")
                return jsonify({"status": "invalid date format"}), 400

            diff_ms = due_date - start_date
            hours = diff_ms / (1000 * 60 * 60)
            print(f"[INFO] Task {task_id} start and due difference: {hours:.2f} hours")

            if 0 < hours < 24:
                added = add_time_tracked(task_id, start_date, due_date)
                if not added:
                    return jsonify({"status": "failed to add time tracked"}), 500

    except Exception as e:
        print(f"[ERROR] Exception when handling webhook event: {e}")
        return jsonify({"error": "internal server error"}), 500

    return jsonify({"status": "received"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
