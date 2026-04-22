# scripts/gmail_auth.py
# ============================================================
# One-time Gmail OAuth setup script.
# Run this ONCE from the project root to generate token.json.
#
# Prerequisites:
#   1. Google Cloud project with Gmail API enabled
#   2. credentials.json downloaded to the project root
#
# Usage:
#   python scripts/gmail_auth.py
#
# What it does:
#   Opens a browser window for you to authorize access.
#   Saves token.json to the project root.
#   token.json is reused on all future runs — never share it.
# ============================================================

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCOPES           = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_PATH = "credentials.json"
TOKEN_PATH       = "token.json"


def main():
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not os.path.exists(CREDENTIALS_PATH):
        print(f"ERROR: {CREDENTIALS_PATH} not found in project root.")
        print("Download it from Google Cloud Console > APIs & Services > Credentials.")
        sys.exit(1)

    if os.path.exists(TOKEN_PATH):
        print(f"{TOKEN_PATH} already exists. Delete it first if you want to re-authorize.")
        sys.exit(0)

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())

    print(f"Done. {TOKEN_PATH} saved. You can now run the bot.")


if __name__ == "__main__":
    main()
