# weekly_summary.py

import psycopg2
import pandas as pd
import calendar
from datetime import datetime, timedelta
import warnings
import os

# Suppress all warnings
warnings.filterwarnings("ignore")

PG_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "host.docker.internal"),
    "database": os.getenv("POSTGRES_DB", "clickup"),
    "user": os.getenv("POSTGRES_USER", "mkiel"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
}


def connect_db():
    return psycopg2.connect(**PG_CONFIG)


def load_data(start_date, end_date):
    conn = connect_db()
    query = """
    SELECT folder_name, task_start_date, duration
    FROM clickup_mkiel
    WHERE task_start_date >= %s AND task_start_date <= %s
    ORDER BY task_start_date
    """
    df = pd.read_sql(query, conn, params=[start_date, end_date])
    conn.close()
    df["task_start_date"] = pd.to_datetime(df["task_start_date"])

    # Exclude 'Comarch' (case-insensitive)
    df = df[~df["folder_name"].str.lower().eq("comarch")]
    return df


def time_str_to_hours(time_str):
    if not time_str or time_str == "0:00":
        return 0.0
    h, m = time_str.split(":")
    return int(h) + int(m) / 60


def hours_to_hm(hours_float):
    negative = hours_float < 0
    hours_float = abs(hours_float)
    hours = int(hours_float)
    minutes = int(round((hours_float - hours) * 60))
    if minutes == 60:
        hours += 1
        minutes = 0
    hm_str = f"{hours}:{minutes:02d}"
    return f"-{hm_str}" if negative else hm_str


def build_month_df(df_weekly, year, month):
    month_start = pd.Timestamp(year=year, month=month, day=1)
    month_end = pd.Timestamp(
        year=year, month=month, day=calendar.monthrange(year, month)[1]
    )
    month_dates = pd.date_range(start=month_start, end=month_end, freq="D").date

    folders = sorted(df_weekly["folder_name"].dropna().unique())
    folder_index = [f.capitalize() for f in folders]

    date_strs = [d.strftime("%Y-%m-%d") for d in month_dates]
    month_df = pd.DataFrame(index=folder_index, columns=date_strs)

    def format_duration(ms):
        total_minutes = ms // (1000 * 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}:{minutes:02d}" if hours or minutes else "0:00"

    for folder in folders:
        folder_df = df_weekly[df_weekly["folder_name"].str.lower() == folder.lower()]
        daily_totals = folder_df.groupby(folder_df["task_start_date"].dt.date)[
            "duration"
        ].sum()
        for d in month_dates:
            dur = daily_totals.get(d, 0)
            month_df.loc[folder.capitalize(), d.strftime("%Y-%m-%d")] = format_duration(
                dur
            )

    month_df.index.name = "Folder Name"
    return month_df


def create_weekly_summary_df(month_df, month_start_str, month_end_str):
    month_start = datetime.strptime(month_start_str, "%Y-%m-%d")
    month_end = datetime.strptime(month_end_str, "%Y-%m-%d")

    days_until_monday = (7 - month_start.weekday()) % 7
    first_monday = month_start + timedelta(days=days_until_monday)

    if not pd.api.types.is_datetime64_any_dtype(month_df.columns):
        month_df.columns = pd.to_datetime(month_df.columns)

    folders = month_df.index.tolist()
    data = {}

    current_start = first_monday
    while current_start <= month_end:
        current_end = current_start + timedelta(days=6)
        if current_end > month_end:
            current_end = month_end

        week_label = f"{current_start.strftime('%Y-%m-%d')}_to_{current_end.strftime('%Y-%m-%d')}"
        data[week_label] = []

        for folder in folders:
            durations = month_df.loc[folder]
            filtered = durations[
                (durations.index >= current_start) & (durations.index <= current_end)
            ]
            sum_hours = sum(time_str_to_hours(dur) for dur in filtered)
            data[week_label].append(sum_hours)

        current_start = current_end + timedelta(days=1)

    weekly_summary_df = pd.DataFrame(data, index=folders)
    weekly_summary_df["total"] = weekly_summary_df.sum(axis=1)
    return weekly_summary_df


def convert_summary_to_hhmm(df):
    df_hhmm = df.copy()
    for col in df_hhmm.columns:
        df_hhmm[col] = df_hhmm[col].apply(hours_to_hm)
    return df_hhmm
