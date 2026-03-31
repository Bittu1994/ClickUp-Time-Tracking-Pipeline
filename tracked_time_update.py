import requests
from datetime import datetime, timedelta
import os

CLICKUP_TOKEN = os.getenv("CLICKUP_API_KEY")
if not CLICKUP_TOKEN:
    raise ValueError("Missing required env var: CLICKUP_API_KEY")
TEAM_ID = os.getenv("CLICKUP_TEAM_ID")
if not TEAM_ID:
    raise ValueError("Missing required env var: CLICKUP_TEAM_ID")
HEADERS = {"Authorization": CLICKUP_TOKEN, "Content-Type": "application/json"}


def get_spaces(team_id):
    url = f"https://api.clickup.com/api/v2/team/{team_id}/space"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("spaces", [])


def get_folders(space_id):
    url = f"https://api.clickup.com/api/v2/space/{space_id}/folder"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("folders", [])


def get_lists(folder_id):
    url = f"https://api.clickup.com/api/v2/folder/{folder_id}/list"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("lists", [])


def get_lists_in_space(space_id):
    url = f"https://api.clickup.com/api/v2/space/{space_id}/list"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("lists", [])


def get_tasks_from_list(list_id, due_date_gt=None, due_date_lt=None):
    tasks = []
    page = 0
    while True:
        url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
        params = {
            "page": page,
            "order_by": "created",
            "reverse": False,
            "include_closed": "true",
        }
        if due_date_gt is not None:
            params["due_date_gt"] = due_date_gt
        if due_date_lt is not None:
            params["due_date_lt"] = due_date_lt

        resp = requests.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("tasks", [])
        if not batch:
            break
        tasks.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return tasks


def get_time_tracked(task_id, task_name):
    url = f"https://api.clickup.com/api/v2/task/{task_id}/time"
    resp = requests.get(url, headers=HEADERS)
    if resp.ok:
        data = resp.json()
        total_time = sum(entry.get("time", 0) for entry in data.get("data", []))
        return total_time
    else:
        print(
            f"[ERROR] Failed to fetch time tracked for task '{task_name}' (ID: {task_id}): {resp.status_code}"
        )
        return 0


def add_time_tracked(task_id, start_ms, end_ms, task_name):
    url = f"https://api.clickup.com/api/v2/task/{task_id}/time"
    duration_ms = end_ms - start_ms
    payload = {
        "start": start_ms,
        "end": end_ms,
        "duration": duration_ms,
        "description": "Auto time tracked based on start and due date difference",
    }
    resp = requests.post(url, json=payload, headers=HEADERS)
    if resp.ok:
        print(f"[INFO] Added time tracked to task '{task_name}' (ID: {task_id})")
    else:
        print(
            f"[ERROR] Failed to add time tracked for task '{task_name}' (ID: {task_id}): {resp.status_code} {resp.text}"
        )


def ms_to_hm(ms):
    total_minutes = ms // (1000 * 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}:{minutes:02d}"


def main(range_start: datetime, range_end: datetime):

    range_start_ms = int(range_start.timestamp() * 1000)
    range_end_ms = int(range_end.timestamp() * 1000)
    print("[INFO] Fetching all spaces...")
    spaces = get_spaces(TEAM_ID)

    all_tasks = []
    for space in spaces:
        space_id = space["id"]
        print(f"[INFO] Processing space: {space['name']} ({space_id})")

        folders = get_folders(space_id)
        lists = get_lists_in_space(space_id)

        for folder in folders:
            folder_lists = get_lists(folder["id"])
            lists.extend(folder_lists)

        print(f"[INFO] Found {len(lists)} lists in space {space['name']}")

        for lst in lists:
            list_id = lst["id"]
            print(f"[INFO] Fetching tasks from list: {lst['name']} ({list_id})")
            # Pass date range to filter tasks fetched
            tasks = get_tasks_from_list(
                list_id, due_date_gt=range_start_ms, due_date_lt=range_end_ms
            )
            all_tasks.extend(tasks)

    print(f"[INFO] Total tasks fetched: {len(all_tasks)}")

    for task in all_tasks:
        task_id = task["id"]
        task_name = task.get("name", "<No Name>")

        created_date = task.get("date_created")
        if created_date is None:
            continue
        if isinstance(created_date, str):
            try:
                created_date = int(created_date)
            except ValueError:
                print(
                    f"[WARN] Task '{task_name}' (ID: {task_id}) has invalid created_date: {created_date}"
                )
                continue

        if not (range_start_ms <= created_date <= range_end_ms):
            continue

        start_date = task.get("start_date")
        due_date = task.get("due_date")

        if start_date is None or due_date is None:
            print(
                f"[WARN] Task '{task_name}' (ID: {task_id}) missing start or due date"
            )
            continue

        for field_name, field_value in [
            ("start_date", start_date),
            ("due_date", due_date),
        ]:
            if isinstance(field_value, str):
                if field_value.isdigit():
                    try:
                        field_value = int(field_value)
                    except ValueError:
                        field_value = None
                else:
                    field_value = None
            elif not isinstance(field_value, int):
                field_value = None

            if field_name == "start_date":
                start_date = field_value
            else:
                due_date = field_value

        if start_date is None or due_date is None:
            print(
                f"[WARN] Task '{task_name}' (ID: {task_id}) has invalid start or due date"
            )
            continue

        time_tracked = get_time_tracked(task_id, task_name)
        if time_tracked > 0:
            continue

        diff_ms = due_date - start_date
        diff_hours = diff_ms / (1000 * 60 * 60)

        if 0 < diff_hours <= 24:
            add_time_tracked(task_id, start_date, due_date, task_name)
            start_dt = datetime.fromtimestamp(start_date / 1000)
            due_dt = datetime.fromtimestamp(due_date / 1000)
            added_time_str = ms_to_hm(diff_ms)
            print(
                f"[ADDED] Task: '{task_name}' (ID: {task_id}) | Start: {start_dt} | Due: {due_dt} | Added Time: {added_time_str}"
            )
        else:
            print(
                f"[INFO] Task '{task_name}' (ID: {task_id}) duration {diff_hours:.2f}h not in (0,24] hours, skipping."
            )


if __name__ == "__main__":
    main()