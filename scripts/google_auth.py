from google_auth_oauthlib.flow import InstalledAppFlow
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.readonly",
]

flow = InstalledAppFlow.from_client_secrets_file(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "google_client_secret.json"),
    SCOPES,
)

try:
    creds = flow.run_local_server(
        port=8765,
        access_type="offline",
        prompt="consent",
    )
except OSError as e:
    print(f"Local server failed ({e}); falling back to console mode.")
    creds = flow.run_console()

if not creds.refresh_token:
    raise SystemExit(
        "No refresh_token returned. Go to https://myaccount.google.com/permissions, "
        "remove the app, and run this script again."
    )

print("\n=== העתק את הערכים האלה ===")
print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
print(f"GOOGLE_CLIENT_ID={creds.client_id}")
print(f"GOOGLE_CLIENT_SECRET={creds.client_secret}")
