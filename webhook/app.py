from flask import Flask, request, jsonify
import requests
import os
import sys
from pathlib import Path
from datetime import datetime

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from database import connect_db, create_tables_if_not_exists, insert_entries_to_db
from folder_config import map_folder_name_from_task

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


def upsert_duration_to_local_db(task_id, task_details, start_ms, end_ms):
    """Store duration (due - start) in clickup_mkiel; no ClickUp Time Tracking API."""
    duration_ms = end_ms - start_ms
    hours = duration_ms / (1000 * 60 * 60)
    if not (0 < hours <= 24):
        print(f"[INFO] Task {task_id} duration {hours:.2f}h out of range, skip DB.")
        return True
    task_start_date = datetime.fromtimestamp(start_ms / 1000).date()
    entry = {
        "task_id": str(task_id),
        "folder_name": map_folder_name_from_task(task_details),
        "task_start_date": task_start_date,
        "duration": duration_ms,
    }
    conn = connect_db()
    try:
        create_tables_if_not_exists(conn)
        insert_entries_to_db(conn, [entry])
    finally:
        conn.close()
    print(f"[INFO] Upserted task {task_id} into clickup_mkiel")
    return True


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

            if 0 < hours <= 24:
                upsert_duration_to_local_db(task_id, task_details, start_date, due_date)

    except Exception as e:
        print(f"[ERROR] Exception when handling webhook event: {e}")
        return jsonify({"error": "internal server error"}), 500

    return jsonify({"status": "received"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
