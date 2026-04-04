import requests
import time
import psycopg2
from psycopg2 import sql as psql
import pandas as pd
import csv
import os
import shutil
import subprocess
from datetime import datetime

from folder_config import map_folder_name_from_task

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

                folder_name = map_folder_name_from_task(task)
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
_BACKUP_ALLOWED_TABLES = frozenset({"clickup_mkiel"})


def backup_table_to_csv(conn, table_name):
    """Dump all rows of a whitelisted table to database_backup_csv/. Returns file path."""
    if table_name not in _BACKUP_ALLOWED_TABLES:
        raise ValueError(f"Backup not allowed for table: {table_name!r}")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = "database_backup_csv"
    os.makedirs(backup_dir, exist_ok=True)
    csv_filename = os.path.join(backup_dir, f"{table_name}_backup_{timestamp}.csv")
    with conn.cursor() as cur:
        cur.execute(psql.SQL("SELECT * FROM {}").format(psql.Identifier(table_name)))
        rows = cur.fetchall()
        headers = [desc[0] for desc in cur.description]
    with open(csv_filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"Backup of {table_name} saved to {csv_filename}")
    return csv_filename


def backup_clickup_mkiel_to_csv():
    """Connect, ensure table exists, write CSV backup. Returns path to CSV."""
    conn = connect_db()
    try:
        create_tables_if_not_exists(conn)
        return backup_table_to_csv(conn, "clickup_mkiel")
    finally:
        conn.close()


def backup_database_pg_dump():
    """
    Full logical backup via pg_dump (custom format, restorable with pg_restore).
    Uses POSTGRES_* / PG_CONFIG. Requires `pg_dump` on PATH (e.g. postgresql-client).
    """
    if os.getenv("SKIP_PG_DUMP", "").strip().lower() in ("1", "true", "yes"):
        raise RuntimeError("pg_dump skipped (SKIP_PG_DUMP is set)")
    pg_dump = shutil.which("pg_dump")
    if not pg_dump:
        raise RuntimeError(
            "pg_dump not found on PATH. Install PostgreSQL client tools "
            "(macOS: brew install libpq && link, Debian/Ubuntu: postgresql-client, "
            "or use Docker image which includes them)."
        )
    backup_dir = "database_backup_pg"
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dbname = PG_CONFIG["database"]
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in dbname)
    out_path = os.path.join(backup_dir, f"{safe}_{timestamp}.dump")

    env = os.environ.copy()
    env["PGPASSWORD"] = PG_CONFIG["password"] if PG_CONFIG["password"] is not None else ""

    cmd = [
        pg_dump,
        "-h",
        PG_CONFIG["host"],
        "-p",
        str(PG_CONFIG["port"]),
        "-U",
        PG_CONFIG["user"],
        "-d",
        PG_CONFIG["database"],
        "-F",
        "c",
        "-f",
        out_path,
        "--no-owner",
        "--no-acl",
    ]
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"pg_dump failed (exit {result.returncode}): {err}")
    print(f"pg_dump saved to {out_path}")
    return out_path


def try_backup_database_pg_dump():
    """Run pg_dump; on failure print warning and return None (non-fatal)."""
    try:
        return backup_database_pg_dump()
    except RuntimeError as e:
        print(f"[WARN] pg_dump: {e}")
        return None

# === MAIN ===
def main():
    conn = connect_db()
    print("Connected to PostgreSQL database!")

    create_tables_if_not_exists(conn)

    # Backup before making any changes
    backup_table_to_csv(conn, "clickup_mkiel")
    try_backup_database_pg_dump()

    entries = fetch_valid_tasks()
    insert_entries_to_db(conn, entries)

    conn.close()
    print("Done.")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "backup":
            path = backup_clickup_mkiel_to_csv()
            print(f"Done. CSV: {path}")
        elif cmd in ("backup-pg", "backup_pg"):
            path = backup_database_pg_dump()
            print(f"Done. pg_dump: {path}")
        else:
            print("Usage: python database.py [backup|backup-pg]")
            raise SystemExit(2)
    else:
        main()
