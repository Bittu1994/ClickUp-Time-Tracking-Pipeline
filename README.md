# ClickUp Time Tracking Pipeline

**License:** This repository is **not** open source. Personal, non-commercial use is allowed. Commercial use, monetization, redistribution, and production use in paid products/services are prohibited. See [`LICENSE`](LICENSE) for full terms.

---

## Why I built this

I rely on ClickUp for personal task and time management, but the **built-in time tracking did not match how I wanted hours recorded and summarized**—and the **workflow I needed was either awkward in the product or gated behind paid tiers** (depending on how ClickUp changed features over time). Rather than fight the UI or pay for a bundle of features I did not need, I **built a small custom pipeline** tailored to my own categories and reporting style.

This project:

- **Syncs** tasks and durations from the ClickUp API into a **PostgreSQL** database I control.
- **Derives** weekly and monthly rollups the way I define them (folders, tags, planned vs actual hours).
- **Exports** rich **Excel** workbooks (and a **Streamlit** UI) so I can review habits and work blocks outside ClickUp.
- Optionally **pushes** outputs to **Google Drive** and reacts to **webhooks** for automation.

**Rough build period:** July–December 2025 (~3–4 months of evenings/weekends), iterated as my own needs evolved.

---

## What’s in the repo

- `database.py` — fetch tasks from ClickUp, upsert into Postgres (durations from task dates such as start/due, not ClickUp’s paid Time Tracking API).
- `folder_config.py` — folder name map, planned hours, productivity/enjoyment tags (single place to customize).
- `main.py` — Streamlit app plus Excel generation (planned vs actual, productivity vs enjoyment buckets). In the report section, **export and Google Drive actions appear above the preview table**; the folder filter still applies to both the workbook and the table.
- `weekly_summary.py` — monthly/weekly aggregation logic shared by the UI (parameterized SQL).
- `webhook/` — optional Flask receiver (`webhook/app.py`) and launcher (`webhook/main.py`) for task events.
- `tracked_time_update.py` — date-range sync from the ClickUp task API into Postgres (CSV snapshot before upsert), using the same duration rules as the full fetch.
- `styling.py` — Excel formatting (including folder tag colors driven by `folder_config.py`).
- Docker + `docker-compose` for a repeatable local run (Postgres client in the image for optional `pg_dump` backups).

### CI

GitHub Actions (`.github/workflows/ci.yml`) runs on pushes and PRs to `main` / `master`: `compileall` on the Python modules plus `python -m unittest discover -s tests` (no API keys required).

## Personalized setup note

This project is personalized for my own workflow. Some parts are intentionally hardcoded (for example folder/category names, preferred order in reports, planned hours, tags, and fixed report date ranges). Lists are not fully dynamic by default.

If you want to use it for your own personal workflow, start with **`folder_config.py`** and **`main.py`** (date ranges, folder order in Excel), plus **`styling.py`** for Excel colors.

### Google Drive upload (OAuth)

`google_auth.py` opens a **local browser** to build `token.pickle`. That flow usually fails inside Docker (redirect goes to your Mac’s `localhost`, not the container). Easiest path: run the OAuth step **once on the host** (venv + `python -c "from google_auth import get_user_credentials; get_user_credentials()"`), then ensure `token.pickle` and `oauth_client.json` are available to the app (mount a volume or copy into the image).

### GitHub “Traffic” / clones

GitHub does **not** show *who* cloned the repo. A spike in **clones** with few **unique visitors** often means `git clone`/API/automation (mirrors, scrapers, CI) rather than people clicking the repo page—it is not something you can attribute to “bots vs humans” from the dashboard alone.

## Local setup with `.env`

1. Create your local env file:
   - copy `.env.example` to `.env`
2. Fill in required values:
   - `CLICKUP_API_KEY`
   - `CLICKUP_TEAM_ID`
   - PostgreSQL variables (`POSTGRES_*`)
   - webhook DB variables (`WEBHOOK_POSTGRES_*`) if you use webhook scripts

`.env` is gitignored and should never be committed.

## Run with Docker

```bash
docker compose up --build
```

Streamlit app will be available at:
- [http://localhost:8501](http://localhost:8501)

## Run without Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run main.py
```

## Security checklist before making repo public

- Rotate any API key that was ever hardcoded in past commits.
- Ensure `.env`, `oauth_client.json`, `service_account.json`, and `token.pickle` are not tracked.
- If secrets were committed before, clean git history before publishing.

### Database backups

**CSV (table `clickup_mkiel` only)** — `database_backup_csv/`

- **Full fetch** (`database.py`): CSV snapshot before sync.
- **Range upsert** (`tracked_time_update`): CSV before upsert.
- **Manual**: Streamlit CSV backup button, or `python database.py backup`.

**pg_dump (whole database)** — `database_backup_pg/`, custom format (`.dump`)

- Runs automatically after the CSV step on **full fetch** (if `pg_dump` is available). Set **`SKIP_PG_DUMP=1`** in `.env` to skip (e.g. no client tools on the host).
- **Manual**: Streamlit pg_dump backup button, or `python database.py backup-pg`.
- **Restore** (example; use your DB name and empty target or new DB):

  ```bash
  pg_restore -h localhost -p 5432 -U USER -d clickup --clean --if-exists path/to/clickup_YYYYMMDD_HHMMSS.dump
  ```

Docker image includes **`postgresql-client`** so `pg_dump` works in the container. Compose mounts **`./database_backup_pg`** like the CSV folder.

