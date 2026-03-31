import psycopg2
from tabulate import tabulate

PG_CONFIG = {
    "host": "host.docker.internal",
    "database": "clickup",
    "user": "mkiel",
    "password": "",
    "port": 5432,
}


def connect_db():
    return psycopg2.connect(**PG_CONFIG)


def list_all_data():
    conn = connect_db()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT task_id, folder_name, task_start_date, duration FROM clickup_mkiel ORDER BY task_start_date"
        )
        rows = cur.fetchall()
        headers = [desc[0] for desc in cur.description]

    conn.close()

    print("All data from clickup_mkiel:\n")
    print(tabulate(rows, headers=headers, tablefmt="psql"))


if __name__ == "__main__":
    list_all_data()
