import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google_auth import get_user_credentials


def upload_excel_and_convert(excel_source, filename="habbit_tracker.xlsx", folder_id=None):
    creds = get_user_credentials()
    drive = build("drive", "v3", credentials=creds)

    # Read bytes
    if hasattr(excel_source, "read"):
        data = excel_source.read()
    else:
        data = excel_source.getvalue()

    media = MediaIoBaseUpload(
        io.BytesIO(data),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        resumable=False,
    )

    file_metadata = {
        "name": filename,
        "mimeType": "application/vnd.google-apps.spreadsheet",
    }

    # 👇 THIS is the only new logic
    if folder_id:
        file_metadata["parents"] = [folder_id]

    file = drive.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink",
    ).execute()

    return file["webViewLink"]
