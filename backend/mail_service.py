import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")


SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def get_gmail_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES
            )

            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build(
        "gmail",
        "v1",
        credentials=creds
    )


def get_inbox_mails(max_results=20):
    service = get_gmail_service()

    result = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        maxResults=max_results
    ).execute()

    messages = result.get("messages", [])

    mails = []

    for message in messages:
        msg = service.users().messages().get(
            userId="me",
            id=message["id"],
            format="metadata",
            metadataHeaders=[
                "From",
                "Subject",
                "Date"
            ]
        ).execute()

        headers = msg.get("payload", {}).get("headers", [])

        mail = {
            "id": msg.get("id"),
            "from": "",
            "subject": "(Kein Betreff)",
            "date": "",
            "snippet": msg.get("snippet", "")
        }

        for header in headers:
            name = header.get("name")
            value = header.get("value", "")

            if name == "From":
                mail["from"] = value

            elif name == "Subject":
                mail["subject"] = value

            elif name == "Date":
                mail["date"] = value

        mails.append(mail)

    return mails