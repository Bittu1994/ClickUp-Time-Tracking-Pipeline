import requests
import time
import psycopg2
import pandas as pd
import csv
from datetime import datetime
import os

API_KEY = os.getenv("CLICKUP_API_KEY")
if not API_KEY:
    raise ValueError("Missing required env var: CLICKUP_API_KEY")
HEADERS = {"Authorization": API_KEY, "Content-Type": "application/json"}
TEAM_ID = os.getenv("CLICKUP_TEAM_ID")
if not TEAM_ID:
    raise ValueError("Missing required env var: CLICKUP_TEAM_ID")

PG_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "host.docker.internal"),
    "database": os.getenv("POSTGRES_DB", "clickup"),
    "user": os.getenv("POSTGRES_USER", "mkiel"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
}

# === DB Setup ===
def connect_db():
    return psycopg2.connect(**PG_CONFIG)

def create_tables_if_not_exists(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clickup_mkiel (
                task_id VARCHAR PRIMARY KEY,
                folder_name VARCHAR,
                task_start_date DATE,
                duration BIGINT
            );
        """)
    conn.commit()
    print("Ensured clickup_mkiel table exists.")

# === ClickUp API Hierarchy ===
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

def get_tasks_from_list(list_id):
    tasks = []
    page = 0
    while True:
        url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
        params = {
            "page": page,
            "include_closed": "true"
        }
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
        time.sleep(0.2)
    return tasks

# === Task Processing ===
def fetch_valid_tasks():
    print("Fetching all tasks from all spaces/folders/lists...")

    spaces = get_spaces(TEAM_ID)
    task_data = []
    all_raw_folders = set()
    all_mapped_folders = set()

    for space in spaces:
        space_id = space["id"]
        folders = get_folders(space_id)
        lists = get_lists_in_space(space_id)

        for folder in folders:
            folder_lists = get_lists(folder["id"])
            lists.extend(folder_lists)

        for lst in lists:
            tasks = get_tasks_from_list(lst["id"])
            for task in tasks:
                task_id = task["id"]
                task_name = task.get("name", "")
                folder_name = task.get("folder", {}).get("name", "") or "N_A"

                all_raw_folders.add(folder_name)

                folder_map = {
                    "Games / PS5": "ComputerGames",
                    "Love life / Tinder ": "LoveLifeTinder",
                    "Job looking / CV": "JobLookingCV",
                    "Master's degree ": "MastersDegree",
                    "Programming / Projects": "ProgrammingProjects",
                    "Cooking": "Cooking",
                    "Comarch": "Comarch",
                    "Comarch Actual Work": "ComarchActualWork",
                    "Guitar": "Guitar",
                    "Gym/Sports": "GymSports",
                    "Improvement": "Improvement",
                    "Audiobook": "Audiobook",
                    "Family Social Life": "FamilySocialLife",
                    "Book": "Book",
                    "Watching Serials / Movies / Football games": "TvShows",
                    "Social life": "SocialLife"
                }
                folder_name = folder_map.get(folder_name, folder_name)
                all_mapped_folders.add(folder_name)

                start = task.get("start_date")
                due = task.get("due_date")

                if not (start and due and str(start).isdigit() and str(due).isdigit()):
                    continue

                start_ms = int(start)
                due_ms = int(due)

                duration_ms = due_ms - start_ms
                duration_hours = duration_ms / (1000 * 60 * 60)

                if not (0 < duration_hours <= 24):
                    continue

                start_date = pd.to_datetime(start_ms, unit="ms").date()

                task_data.append({
                    "task_id": task_id,
                    "folder_name": folder_name,
                    "task_start_date": start_date,
                    "duration": duration_ms
                })

    print(f"\nUnique raw folders found:")
    for f in sorted(all_raw_folders):
        print(f" - '{f}'")
    print(f"\nMapped folders:")
    for f in sorted(all_mapped_folders):
        print(f" - {f}")

    return task_data

# === DB Insertion ===
def insert_entries_to_db(conn, entries):
    with conn.cursor() as cur:
        insert_query = """
        INSERT INTO clickup_mkiel (task_id, folder_name, task_start_date, duration)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (task_id) DO UPDATE SET
            folder_name = EXCLUDED.folder_name,
            task_start_date = EXCLUDED.task_start_date,
            duration = EXCLUDED.duration
        """
        data_tuples = [(e['task_id'], e['folder_name'], e['task_start_date'], e['duration']) for e in entries]
        cur.executemany(insert_query, data_tuples)
    conn.commit()
    print(f"\nInserted/Updated {len(entries)} entries into the database.")

# === DB Backup ===
def backup_table_to_csv(conn, table_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = "database_backup_csv"
    os.makedirs(backup_dir, exist_ok=True)
    csv_filename = os.path.join(backup_dir, f"{table_name}_backup_{timestamp}.csv")
    with conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {table_name}")
        rows = cur.fetchall()
        headers = [desc[0] for desc in cur.description]
    with open(csv_filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"Backup of {table_name} saved to {csv_filename}")

# === MAIN ===
def main():
    conn = connect_db()
    print("Connected to PostgreSQL database!")

    create_tables_if_not_exists(conn)

    # Backup before making any changes
    backup_table_to_csv(conn, "clickup_mkiel")

    entries = fetch_valid_tasks()
    insert_entries_to_db(conn, entries)

    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()
