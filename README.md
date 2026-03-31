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

- `database.py` — fetch tasks from ClickUp, normalize folder names, upsert into Postgres.
- `main.py` — Streamlit app plus Excel generation (planned vs actual, productivity vs enjoyment buckets).
- `weekly_summary.py` — monthly/weekly aggregation logic shared by the UI.
- `webhook/` — optional Flask receiver + webhook registration for task events.
- `tracked_time_update.py` — helper logic around ClickUp time entries where the stock flow was insufficient.
- Docker + `docker-compose` for a repeatable local run.

## Personalized setup note

This project is personalized for my own workflow. Some parts are intentionally hardcoded (for example folder/category names, preferred order in reports, planned hours, tags, and fixed report date ranges). Lists are not fully dynamic by default.

If you want to use it for your own personal workflow, update those variables to match your own ClickUp structure and reporting style.

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

