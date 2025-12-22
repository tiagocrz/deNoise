import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pathlib import Path

# Define your required Gmail API scopes
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
                # 1. Attempt to refresh the access token
                creds.refresh(Request())
            except Exception as e:
                # 2. Refresh failed (Refresh Token is expired/revoked)
                print(f"Token refresh failed ({e}): Requesting new authorization...")
                creds = None # <-- IMPORTANT: Set creds to None to force full re-auth
        
        # 3. If creds is None (either first run or refresh failed), run full OAuth flow
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(
                port=0,
                access_type='offline',
                prompt='consent' # ensures new refresh token is granted
            )
        
        # Save new credentials for future runs (this also runs if refresh succeeded above)
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    # Build and return the Gmail API service
    service = build("gmail", "v1", credentials=creds)
    return service