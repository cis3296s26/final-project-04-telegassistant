# ai/gmail_client.py
# ============================================================
# TeleGAssistant — Gmail Client
# Owned by: AI Engineer
# ============================================================

import asyncio
import os
from datetime import datetime, timedelta

TOKEN_PATH       = "token.json"
CREDENTIALS_PATH = "credentials.json"
SCOPES           = ["https://www.googleapis.com/auth/gmail.readonly"]
MAX_EMAILS       = 20


def _fetch_emails_sync() -> list[dict] | None:
    """Blocking Gmail API calls — run via asyncio.to_thread."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        if not os.path.exists(TOKEN_PATH):
            return None

        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_PATH, "w") as f:
                f.write(creds.to_json())

        service = build("gmail", "v1", credentials=creds)

        since = (datetime.now() - timedelta(days=3)).strftime("%Y/%m/%d")
        query = f"is:unread after:{since} -category:promotions -category:social"

        result = service.users().messages().list(
            userId="me", q=query, maxResults=MAX_EMAILS
        ).execute()

        messages = result.get("messages", [])
        if not messages:
            return []

        emails = []
        for msg in messages:
            detail = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            ).execute()

            headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
            sender  = headers.get("From", "Unknown")
            subject = headers.get("Subject", "(no subject)")
            snippet = detail.get("snippet", "")[:120]

            if "<" in sender:
                sender = sender[:sender.index("<")].strip().strip('"')

            emails.append({
                "from":    sender,
                "subject": subject,
                "snippet": snippet,
            })

        return emails

    except Exception:
        return None


def is_connected() -> bool:
    return os.path.exists(TOKEN_PATH)


async def get_recent_emails() -> list[dict] | None:
    return await asyncio.to_thread(_fetch_emails_sync)
