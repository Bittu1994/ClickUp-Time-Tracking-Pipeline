import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os

DB_CONFIG = {
    "host": os.getenv("WEBHOOK_POSTGRES_HOST", os.getenv("POSTGRES_HOST", "host.docker.internal")),
    "port": int(os.getenv("WEBHOOK_POSTGRES_PORT", os.getenv("POSTGRES_PORT", "5432"))),
    "dbname": os.getenv("WEBHOOK_POSTGRES_DB", "clickup_webhooks"),
    "user": os.getenv("WEBHOOK_POSTGRES_USER", "clickup_user"),
    "password": os.getenv("WEBHOOK_POSTGRES_PASSWORD"),
}


def connect_db():
    # Connect as the target user to the target DB (no password)
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )


def setup_db():

    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tracked_tasks (
            id SERIAL PRIMARY KEY,
            task_id TEXT UNIQUE,
            name TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            tracked_hours FLOAT,
            raw_payload JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    )
    conn.commit()
    cur.close()
    conn.close()
    print("✅ DB ready.")


if __name__ == "__main__":
    setup_db()
