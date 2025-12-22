import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pathlib import Path

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """
    Returns an authenticated Gmail API service object.
    Handles token creation, refresh, and regeneration.
    """
    creds = None
    script_dir = Path(__file__).resolve().parent
    token_path = script_dir / "token.json"
    credentials_path = script_dir / "credentials.json"

    # Load saved credentials if they exist
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid credentials, refresh or authenticate again
    if not creds or not creds.valid:
        
        # Check if we have credentials to attempt a refresh
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Token refresh failed ({e}): Requesting new authorization...")
                creds = None
        
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(
                port=0,
                access_type='offline',
                prompt='consent'
            )
        
        # Save new credentials for future runs
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service