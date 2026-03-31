from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os

SCOPES = ["https://www.googleapis.com/auth/drive"]

def get_user_credentials():
    creds = None

    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "oauth_client.json",
                SCOPES,
            )
            creds = flow.run_local_server(
                port=0,
                access_type="offline",
                prompt="consent",
            )

        with open("token.pickle", "wb") as f:
            pickle.dump(creds, f)

    return creds
