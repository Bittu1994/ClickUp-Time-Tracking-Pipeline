import streamlit as st
import psycopg2
import pandas as pd
import io
import calendar
from datetime import datetime, timedelta
import warnings
from styling import get_formats
from tracked_time_update import main as tracked_time_update
from styling import get_formats  # import your external formats
import os


import os


# if "oauth_token_deleted" not in st.session_state:
#     if os.path.exists("token.pickle"):
#         os.remove("token.pickle")
#     st.session_state["oauth_token_deleted"] = True


# Range of exel months to waht date will the exel show 
fixed_start_date = "2025-06-01"
fixed_end_date = "2026-02-28"


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


def check_connection_info():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT current_database(), current_user, current_schema();")
    dbname, user, schema = cur.fetchone()
    cur.close()
    conn.close()
    return dbname, user, schema


def load_data(start_date, end_date):
    conn = connect_db()
    query = f"""
    SELECT folder_name, task_start_date, duration
    FROM clickup_mkiel
    WHERE task_start_date >= '{start_date}' AND task_start_date <= '{end_date}'
    ORDER BY task_start_date
    """
    df = pd.read_sql(query, conn)
    conn.close()
    df["task_start_date"] = pd.to_datetime(df["task_start_date"])
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


from weekly_summary import (
    load_data,
    build_month_df,
    create_weekly_summary_df,
    convert_summary_to_hhmm,
)


# Load raw task data
df_weekly = load_data(fixed_start_date, fixed_end_date)


# Helper to iterate months inclusive between two dates
def months_between(start_str, end_str):
    start = datetime.strptime(start_str, "%Y-%m-%d").date()
    end = datetime.strptime(end_str, "%Y-%m-%d").date()
    months = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        months.append((y, m))
        if m == 12:
            m = 1
            y += 1
        else:
            m += 1
    return months


# Build monthly and weekly summaries dynamically for the range
MONTH_DFS = {}
WEEKLY_SUMMARIES = {}  # maps (year, month) -> weekly_summary (HH:MM strings)

for yy, mm in months_between(fixed_start_date, fixed_end_date):
    month_df = build_month_df(df_weekly, yy, mm)
    MONTH_DFS[(yy, mm)] = month_df

    month_start = f"{yy}-{mm:02d}-01"
    month_end = f"{yy}-{mm:02d}-{calendar.monthrange(yy, mm)[1]}"
    weekly = create_weekly_summary_df(month_df, month_start, month_end)
    WEEKLY_SUMMARIES[(yy, mm)] = convert_summary_to_hhmm(weekly)

print("Generated monthly/weekly summaries for:", sorted(list(WEEKLY_SUMMARIES.keys())))


def format_duration(ms):
    total_minutes = ms // (1000 * 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}:{minutes:02d}" if hours or minutes else "0:00"


def create_all_folders_daily_summary_excel(writer, df, start_date, end_date):

    all_dates = pd.date_range(start=start_date, end=end_date).date
    folders = sorted(df["folder_name"].dropna().unique())
    folder_index = [f.capitalize() for f in folders]
    workbook = writer.book
    # ✅ Load formats here
    f = get_formats(workbook)
    worksheet = workbook.add_worksheet("All Folders Daily Summary")
    writer.sheets["All Folders Daily Summary"] = worksheet
    worksheet.set_column(0, 0, f.get("folder_column_width"))

    # Get all formats from external module
    f = get_formats(workbook)

    dates_by_month = {}
    for d in all_dates:
        dates_by_month.setdefault((d.year, d.month), []).append(d)

    start_row = 0

    def format_duration(ms):
        total_minutes = ms // (1000 * 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}:{minutes:02d}" if hours or minutes else "0:00"

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

    for (year, month), month_dates in sorted(dates_by_month.items(), reverse=True):
        month_name = calendar.month_name[month] + f" {year}"
        date_strs = [d.strftime("%Y-%m-%d") for d in month_dates]

        # preferred_order = ["MastersDegree", "ProgrammingProjects", "Guitar", "Reading", "Cooking", "JobLookingCV", "GamesPS5", "Fitual", "Cooking", "Finance", "Improvement", "Lovelifetinder", "SocialLife", "TvShows", "Gymsports"]
        preferred_order = [
            "ComarchActualWork",
            "ProgrammingProjects",
            "Improvement",
            "Cooking",
            "Guitar",
            "Audiobook",
            "Book",
            "JobLookingCV",
            "Fitual",
            "Finance",
            "GymSports",
            "MastersDegree",
            "LoveLifeTinder",
            "TvShows",
            "ComputerGames",
            "SocialLife",
            "FamilySocialLife",
            "Painting",
            "Carpentering",
        ]

        remaining_folders = [f for f in folders if f not in preferred_order]
        folders = preferred_order + remaining_folders

        # # Drop "Comarch" from final list
        # folders = [f for f in folders if f.lower() != "comarch"]

        # Create the DataFrame with your preferred ordered folders as index
        month_df = pd.DataFrame(
            index=[f.capitalize() for f in folders], columns=date_strs
        )

        for folder in folders:
            folder_df = df[df["folder_name"].str.lower() == folder.lower()]
            daily_totals = folder_df.groupby(folder_df["task_start_date"].dt.date)[
                "duration"
            ].sum()
            for d in month_dates:
                dur = daily_totals.get(d, 0)
                month_df.loc[folder.capitalize(), d.strftime("%Y-%m-%d")] = (
                    format_duration(dur)
                )

        month_df.index.name = "Folder Name"
        worksheet.write(start_row, 0, month_name, f["bold_format"])

        first_date_col = 1

        first_day = month_dates[0]
        first_monday = first_day
        while first_monday.weekday() != 0:
            first_monday += pd.Timedelta(days=1)

        weeks = {}
        current_week = 1
        for idx, d in enumerate(month_dates):
            if d < first_monday:
                continue
            if d.weekday() == 0 and d != first_monday:
                current_week += 1
            weeks.setdefault(current_week, []).append(idx)

        for week_num, idxs in weeks.items():
            first_col = first_date_col + idxs[0]
            last_col = first_date_col + idxs[-1]
            worksheet.merge_range(
                start_row + 2,
                first_col,
                start_row + 2,
                last_col,
                f"Week {week_num}",
                f["week_header_format"],
            )

        # Example extra row below Week 1 header
        extra_text = "extra"
        worksheet.write(start_row + 3, first_date_col, extra_text)
        worksheet.write(start_row + 3, first_date_col, extra_text)
        worksheet.write(start_row + 3, first_date_col, extra_text)

        row_1 = [
            "Mastersdegree",
            "Programmingprojects",
            "Guitar",
            "Audiobook",
            "Cooking",
            "JobLookingCV",
            "Gamesps5",
        ]

        # This is the hardcoded actual programming times for 'Programming' row (adjust or generate dynamically if you want)
        # 1. Pick the category for actual programming times, e.g. "Programmingprojects"

        # 2. Extract the row for that category from the weekly summary DataFrame
        # This will be a Series indexed by week columns (e.g. date ranges or week numbers)

        # Use generated WEEKLY_SUMMARIES (built from the data range)
        weekly_summary = WEEKLY_SUMMARIES.get((year, month), pd.DataFrame())
        columns_sorted = (
            list(weekly_summary.columns) if not weekly_summary.empty else []
        )

        for week_num, idxs in weeks.items():
            if len(idxs) < 7:
                continue

            base_col = first_date_col + idxs[0]

            # For each category in row_1, get the value for this week
            row_values = []
            for category in row_1:
                col_idx = week_num - 1
                if col_idx < len(columns_sorted):
                    col_name = columns_sorted[col_idx]
                    try:
                        val = weekly_summary.loc[category, col_name]
                    except KeyError:
                        val = "0:00"
                else:
                    val = "0:00"
                row_values.append(val)

            # Write row_1 headers
            worksheet.write(
                start_row + 3,
                base_col + 0,
                row_1[0],
                f["red_left_border_format_week_sumary_row1"],
            )
            for i in range(1, len(row_1)):
                worksheet.write(
                    start_row + 3, base_col + i, row_1[i], f["row_1_format"]
                )

            # Your static row_2 can stay the same desire times
            row_3 = ["15:00", "5:00", "3:00", "$", "3:00", "2:00", "5:00"]
            worksheet.write(
                start_row + 4,
                base_col + 0,
                row_3[0],
                f["red_left_border_format_week_sumary_row2"],
            )
            for i in range(1, len(row_3)):
                worksheet.write(
                    start_row + 4, base_col + i, row_3[i], f["row_2_format"]
                )

            # Write row_3 with all values from row_values actual times
            for i, val in enumerate(row_values):
                style = (
                    f["red_left_border_format_week_sumary_row3"]
                    if i == 0
                    else f["row_3_format"]
                )
                worksheet.write(start_row + 5, base_col + i, val, style)

        for i, d in enumerate(month_dates):
            fmt = (
                f["red_left_border_date_format_days"]
                if d.weekday() == 0
                else f["date_header_format"]
            )
            worksheet.write(start_row + 6, first_date_col + i, d.day, fmt)

        # Import notes data from external file
        from note_data import notes_mapping

        # Extra "Notes" row under days
        worksheet.write(start_row + 7, 0, "Notes", f["bold_format"])  # Column A label

        # Get notes for this month
        month_key = (year, month)
        current_notes = notes_mapping.get(month_key, [])
        notes_dict = {day: note_data for day, *note_data in current_notes}

        # Map notes to existing format keys in f
        fmt_map = {
            "home": f["home"],
            "work": f["work"],
            "remote": f["remote"],
            "travel": f["travel"]
        }

        for i, d in enumerate(month_dates):
            day_num = d.day
            note_data = notes_dict.get(day_num, None)
            if note_data is None:
                val = ""
                note_type = None
            else:
                note_type = note_data[0]  # First element is always the type
                # If we have a description (tuple of length 2), use it; otherwise use the type
                val = note_data[1] if len(note_data) > 1 else note_type.capitalize()

            # Pick format based on note type, default to f['notes_format']
            fmt = fmt_map.get(note_type, f["notes_format"])

            worksheet.write(start_row + 7, first_date_col + i, val, fmt)

        first_monday_col_idx = None
        for i, d in enumerate(month_dates):
            if d.weekday() == 0:
                first_monday_col_idx = i
                break
        if first_monday_col_idx is None:
            first_monday_col_idx = 7

        for i, folder_name in enumerate(month_df.index):
            fmt = f["folder_name_format_1"] if i % 2 == 0 else f["folder_name_format_2"]
            worksheet.write(start_row + 8 + i, 0, folder_name, fmt)
            for col_idx, date_str in enumerate(month_df.columns):
                val = month_df.at[folder_name, date_str]
                # if (col_idx - first_monday_col_idx) % 7 == 0 and col_idx >= first_monday_col_idx:
                #     cell_fmt = f['red_left_border_format']
                # else:
                cell_fmt = (
                    f["data_cell_format_1"] if i % 2 == 0 else f["data_cell_format_2"]
                )
                worksheet.write(
                    start_row + 8 + i, first_date_col + col_idx, val, cell_fmt
                )

        start_row += 8 + len(month_df) + 2


















        # Summary section below the main table
        summary_start_row = start_row
        worksheet.write(
            summary_start_row, 0, "Summary All Folders Daily", f["bold_format"]
        )

        # Write header for summary
        worksheet.write(summary_start_row + 1, 0, "Folder", f["summary_header_format"])
        worksheet.write(
            summary_start_row + 1, 1, "Planned Time", f["summary_header_format"]
        )
        worksheet.write(
            summary_start_row + 1, 2, "Actual Time", f["summary_header_format"]
        )
        worksheet.write(
            summary_start_row + 1, 3, "Difference", f["summary_header_format"]
        )

        planned_times = {
            "comarchactualwork": 60,
            "programmingprojects": 20,
            "improvement": 15,
            "cooking": 20,
            "guitar": 15,
            "audiobook": 10,
            "book": 10,
            "joblookingcv": 15,
            "fitual": 10,
            "finance": 10,
            "gymsports": 20,
            "mastersdegree": 15,
            
            
            "lovelifetinder": 10,
            
            "tvshows": 10,
            "computergames": 30,
            "sociallife": 50,
            "familysociallife": 30,
            "painting": 10,
            "carpentering": 10,
        }

        # Folder tags (ONLY NEW LOGIC)
        FOLDER_TAGS = {
            "comarchactualwork": {"productivity"},
            "programmingprojects": {"productivity"},
            "improvement": {"productivity"},
            "cooking": {"productivity"},
            "guitar": {"productivity"},
            "audiobook": {"productivity"},
            "book": {"productivity"},
            "joblookingcv": {"productivity"},
            "fitual": {"productivity"},
            "finance": {"productivity"},
            "gymsports": {"productivity"},
            "mastersdegree": {"productivity"},
        

            "lovelifetinder": {"enjoyment"},
            
            "tvshows": {"enjoyment"},
            "computergames": {"enjoyment"},
            "sociallife": {"enjoyment"},
            "familysociallife": {"enjoyment"},
            "painting": {"productivity"},
            "carpentering": {"productivity"},
            
        }

        # After the loop writing folder rows (UNCHANGED)
        for i, folder in enumerate(folders):
            row = summary_start_row + 2 + i
            planned = planned_times.get(folder.lower(), 0)

            df["task_start_date"] = pd.to_datetime(df["task_start_date"])
            df_month = df[
                (df["task_start_date"].dt.year == year)
                & (df["task_start_date"].dt.month == month)
            ]

            folder_df = df_month[df_month["folder_name"].str.lower() == folder.lower()]
            actual = folder_df["duration"].sum() / (
                1000 * 60 * 60
            )

            actual_str = hours_to_hm(actual)
            diff = actual - planned
            diff_str = hours_to_hm(diff)

            worksheet.write(row, 0, folder.capitalize(), f["summary_cell_format"])
            worksheet.write(row, 1, planned, f["summary_cell_format"])
            worksheet.write(row, 2, actual_str, f["summary_cell_format"])

            diff_fmt = (
                f["summary_negative_diff_format"]
                if diff < 0
                else f["summary_cell_format"]
            )
            worksheet.write(row, 3, diff_str, diff_fmt)

        # === Calculate totals for "All" row ===
        total_planned = sum(planned_times.get(folder.lower(), 0) for folder in folders)

        df["task_start_date"] = pd.to_datetime(df["task_start_date"])
        df_month = df[
            (df["task_start_date"].dt.year == year)
            & (df["task_start_date"].dt.month == month)
        ]
        total_actual = df_month["duration"].sum() / (1000 * 60 * 60)

        total_diff = total_actual - total_planned

        all_row = summary_start_row + 2 + len(folders)
        worksheet.write(all_row, 0, "All", f["summary_header_format"])
        worksheet.write(all_row, 1, total_planned, f["summary_header_format"])

        total_actual_str = hours_to_hm(total_actual)
        worksheet.write(all_row, 2, total_actual_str, f["summary_header_format"])

        total_diff_str = hours_to_hm(total_diff)
        diff_fmt = (
            f["summary_negative_diff_format"]
            if total_diff < 0
            else f["summary_header_format"]
        )
        worksheet.write(all_row, 3, total_diff_str, diff_fmt)

        # === Calculate Productivity and Enjoyment (TAG-BASED, SAME VARIABLES) ===
        productivity_planned = 0
        productivity_actual = 0
        enjoyment_planned = 0
        enjoyment_actual = 0

        for folder in folders:
            key = folder.lower()
            planned = planned_times.get(key, 0)

            folder_df = df_month[df_month["folder_name"].str.lower() == key]
            actual = folder_df["duration"].sum() / (1000 * 60 * 60)

            tags = FOLDER_TAGS.get(key, set())

            if "productivity" in tags:
                productivity_planned += planned
                productivity_actual += actual

            if "enjoyment" in tags:
                enjoyment_planned += planned
                enjoyment_actual += actual

        productivity_diff = productivity_actual - productivity_planned
        enjoyment_diff = enjoyment_actual - enjoyment_planned

        # Convert to hh:mm strings
        productivity_actual_str = hours_to_hm(productivity_actual)
        productivity_diff_str = hours_to_hm(productivity_diff)

        enjoyment_actual_str = hours_to_hm(enjoyment_actual)
        enjoyment_diff_str = hours_to_hm(enjoyment_diff)

        # Write the extra rows below "All"
        after_all_row = all_row + 1

        worksheet.write(
            after_all_row + 0,
            0,
            "Productivity sum of hours:",
            f["summary_header_format"],
        )
        worksheet.write(after_all_row + 0, 1, "", f["summary_header_format"])
        worksheet.write(after_all_row + 0, 2, productivity_actual_str, f["summary_header_format"])

        diff_fmt_prod = (
            f["summary_negative_diff_format"]
            if productivity_diff < 0
            else f["summary_header_format"]
        )
        worksheet.write(after_all_row + 0, 3, productivity_diff_str, diff_fmt_prod)

        worksheet.write(
            after_all_row + 1,
            0,
            "Enjoyment sum of hours:",
            f["summary_header_format"],
        )
        worksheet.write(after_all_row + 1, 1, "", f["summary_header_format"])
        worksheet.write(after_all_row + 1, 2, enjoyment_actual_str, f["summary_header_format"])

        diff_fmt_enjoy = (
            f["summary_negative_diff_format"]
            if enjoyment_diff < 0
            else f["summary_header_format"]
        )
        worksheet.write(after_all_row + 1, 3, enjoyment_diff_str, diff_fmt_enjoy)

        start_row = after_all_row + 4




def create_complex_weekly_excel(writer, df):
    # Placeholder – implement your detailed weekly breakdown here if needed
    pass


# --- Streamlit UI ---

st.set_page_config(
    page_title="ClickUp Time Entries - 2025",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 ClickUp Time Entries Report — 2025")

dbname, user, schema = check_connection_info()
st.markdown(
    f"**Connected to database:** `{dbname}`  \n**User:** `{user}`  \n**Schema:** `{schema}`"
)

from database import main as fetch_and_store_data

st.markdown("## Select Date Range for Auto Time Tracking")

default_start = datetime(2026, 1, 1)
default_end = datetime(2026, 1, 7)

range_start = st.date_input("Start Date", value=default_start)
range_end = st.date_input("End Date", value=default_end)

if st.button("🕒 Auto Add Time Tracking (Based on Start–Due Date)"):
    print("Button '🕒 Auto Add Time Tracking' clicked")
    if range_start > range_end:
        st.error("❌ Start date must be before end date.")
    else:
        with st.spinner(f"Running time tracking from {range_start} to {range_end}..."):
            from datetime import datetime  # In case it's not imported already

            tracked_time_update(
                datetime.combine(range_start, datetime.min.time()),
                datetime.combine(range_end, datetime.max.time()),
            )
        st.success("✅ Time tracking completed successfully!")


if st.button("🔄 Fetch & Update Data from ClickUp API"):
    print("Button '🔄 Fetch & Update Data from ClickUp API' clicked")
    with st.spinner("Fetching data and updating database..."):
        fetch_and_store_data()
        st.success("✅ Data fetched and updated successfully!")

# fixed_start_date = "2025-06-01"
# fixed_end_date = "2025-11-30"

try:
    df = load_data(fixed_start_date, fixed_end_date)
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

if df.empty:
    st.info(
        f"No data found between {fixed_start_date} and {fixed_end_date}. Please fetch data first."
    )
else:
    df["Formatted Duration"] = df["duration"].apply(format_duration)
    folder_options = sorted(df["folder_name"].dropna().unique())

    selected_folder = st.selectbox("Filter by Folder", ["All"] + folder_options)

    filtered_df = df.copy()
    if selected_folder != "All":
        filtered_df = filtered_df[filtered_df["folder_name"] == selected_folder]

    st.markdown(
        f"### Displaying entries for **{selected_folder}** from **{fixed_start_date}** to **{fixed_end_date}**"
    )
    st.dataframe(filtered_df[["folder_name", "task_start_date", "Formatted Duration"]])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        create_complex_weekly_excel(writer, filtered_df)
        create_all_folders_daily_summary_excel(
            writer, filtered_df, fixed_start_date, fixed_end_date
        )
    output.seek(0)

    col1, col2 = st.columns(2)

    with col1:
            if st.download_button(
                label="📥 Download Excel Report",
                data=output,
                file_name="habbit_tracker.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ):
                print("Button '📥 Download Excel Report' clicked")

    with col2:
        uploaded_file = st.file_uploader(
            "if you click it will work but you can upload new as well",
            type=["xlsx"],
        )
    
        if st.button("📤 Upload & Convert to Google Sheets"):
                print("Button '📤 Upload & Convert to Google Sheets' clicked")
                try:
                    from drive_upload import upload_excel_and_convert
                    import io

                    if uploaded_file is not None:
                        excel_bytes = uploaded_file.read()
                        filename = uploaded_file.name
                    else:
                        output.seek(0)                 # IMPORTANT
                        excel_bytes = output.getvalue()
                        filename = "habbit_tracker.xlsx"

                    link = upload_excel_and_convert(
                        io.BytesIO(excel_bytes),
                        filename,
                        "1We1WUYqriSpew672xGV-CBkFZK5CgIEB",  # 👈 YOUR DRIVE FOLDER ID
                    )

                    st.success("✅ Uploaded & converted via Google Drive")
                    st.markdown(f"[Open Google Sheet]({link})")
                except Exception as e:
                    st.error(f"Upload failed: {e}")
   

