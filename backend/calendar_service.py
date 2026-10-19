import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

VIENNA = ZoneInfo("Europe/Vienna")


SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def get_calendar_service():
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
        "calendar",
        "v3",
        credentials=creds
    )


def get_upcoming_events(max_results=10):
    service = get_calendar_service()

    now = datetime.now(timezone.utc).isoformat()

    result = service.events().list(
        calendarId="primary",
        timeMin=now,
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    return result.get("items", [])


def get_events_between(start_dt, end_dt):
    """Liefert alle Termine, die den Zeitraum start_dt bis end_dt berühren.
    Datetimes ohne Zeitzone werden als lokale Zeit behandelt."""
    service = get_calendar_service()

    result = service.events().list(
        calendarId="primary",
        timeMin=start_dt.astimezone().isoformat(),
        timeMax=end_dt.astimezone().isoformat(),
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    return result.get("items", [])


def check_calendar_availability(start_datetime, dauer_minuten=60):
    """Prüft, ob ein Zeitraum im Google Kalender frei ist."""

    if dauer_minuten <= 0:
        raise ValueError("Die Dauer muss größer als 0 sein.")

    vienna = ZoneInfo("Europe/Vienna")

    # Naive Uhrzeiten als österreichische Lokalzeit interpretieren
    if start_datetime.tzinfo is None:
        start_datetime = start_datetime.replace(tzinfo=vienna)

    start_datetime = start_datetime.astimezone(vienna)
    end_datetime = start_datetime + timedelta(minutes=dauer_minuten)

    service = get_calendar_service()

    result = service.freebusy().query(
        body={
            "timeMin": start_datetime.isoformat(),
            "timeMax": end_datetime.isoformat(),
            "timeZone": "Europe/Vienna",
            "items": [
                {"id": "primary"}
            ]
        }
    ).execute()

    calendar = result["calendars"]["primary"]

    if calendar.get("errors"):
        raise RuntimeError(
            f"Kalenderprüfung fehlgeschlagen: {calendar['errors']}"
        )

    konflikte = calendar.get("busy", [])

    return {
        "verfuegbar": len(konflikte) == 0,
        "start": start_datetime.isoformat(),
        "ende": end_datetime.isoformat(),
        "konflikte": konflikte,
        "nachricht": (
            "Der gewünschte Zeitraum ist frei."
            if not konflikte
            else "Der gewünschte Zeitraum ist bereits belegt."
        )
    }


def create_event(titel, start_datetime, dauer_minuten=60):
    """Erstellt einen Termin nur, wenn der Zeitraum frei ist."""

    pruefung = check_calendar_availability(
        start_datetime,
        dauer_minuten
    )

    if not pruefung["verfuegbar"]:
        return {
            "erstellt": False,
            "nachricht": "Termin konnte nicht erstellt werden. Zeitraum belegt.",
            "konflikte": pruefung["konflikte"]
        }

    service = get_calendar_service()

    start = datetime.fromisoformat(pruefung["start"])
    ende = datetime.fromisoformat(pruefung["ende"])

    event = {
        "summary": titel,
        "start": {
            "dateTime": start.isoformat(),
            "timeZone": "Europe/Vienna"
        },
        "end": {
            "dateTime": ende.isoformat(),
            "timeZone": "Europe/Vienna"
        }
    }

    erstelltes_event = service.events().insert(
        calendarId="primary",
        body=event
    ).execute()

    return {
        "erstellt": True,
        "nachricht": "Termin wurde erfolgreich erstellt.",
        "termin": erstelltes_event
    }


def _auf_wien(dt):
    """Zeiten ohne Zeitzone gelten als Wiener Zeit, andere werden nach Wien umgerechnet."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=VIENNA)
    return dt.astimezone(VIENNA)


def update_event(event_id, titel=None, start_datetime=None, dauer_minuten=None):
    """Ändert Titel, Startzeit und/oder Dauer eines Termins.
    Bei einer neuen Zeit wird auf Konflikte geprüft. Der Termin selbst zählt dabei nicht als Konflikt."""

    service = get_calendar_service()
    event = service.events().get(calendarId="primary", eventId=event_id).execute()

    aenderungen = {}

    if titel is not None and titel.strip():
        aenderungen["summary"] = titel.strip()

    if start_datetime is not None or dauer_minuten is not None:
        if "dateTime" not in event["start"]:
            return {
                "geaendert": False,
                "nachricht": "Ganztägige Termine können hier nur im Titel geändert werden."
            }

        alter_start = _auf_wien(datetime.fromisoformat(event["start"]["dateTime"]))
        altes_ende = _auf_wien(datetime.fromisoformat(event["end"]["dateTime"]))

        neuer_start = _auf_wien(start_datetime) if start_datetime is not None else alter_start

        if dauer_minuten is not None:
            dauer = dauer_minuten
        else:
            dauer = int((altes_ende - alter_start).total_seconds() // 60)

        if dauer <= 0:
            raise ValueError("Die Dauer muss größer als 0 sein.")

        neues_ende = neuer_start + timedelta(minutes=dauer)

        # Termine im neuen Zeitraum suchen, der Termin selbst und "frei"-Termine zählen nicht
        im_zeitraum = service.events().list(
            calendarId="primary",
            timeMin=neuer_start.isoformat(),
            timeMax=neues_ende.isoformat(),
            singleEvents=True,
            orderBy="startTime"
        ).execute().get("items", [])

        konflikte = [
            {
                "start": e["start"]["dateTime"],
                "end": e["end"]["dateTime"],
                "titel": e.get("summary", "Ohne Titel")
            }
            for e in im_zeitraum
            if e["id"] != event_id
            and "dateTime" in e["start"]
            and e.get("transparency") != "transparent"
        ]

        if konflikte:
            return {
                "geaendert": False,
                "nachricht": "Änderung nicht möglich. Zeitraum belegt.",
                "konflikte": konflikte
            }

        aenderungen["start"] = {"dateTime": neuer_start.isoformat(), "timeZone": "Europe/Vienna"}
        aenderungen["end"] = {"dateTime": neues_ende.isoformat(), "timeZone": "Europe/Vienna"}

    if not aenderungen:
        return {"geaendert": False, "nachricht": "Es gab nichts zu ändern."}

    aktualisiert = service.events().patch(
        calendarId="primary",
        eventId=event_id,
        body=aenderungen
    ).execute()

    return {
        "geaendert": True,
        "nachricht": "Termin wurde geändert.",
        "termin": aktualisiert
    }


def delete_event(event_id):
    """Löscht einen Termin aus dem Google-Kalender."""
    service = get_calendar_service()
    service.events().delete(calendarId="primary", eventId=event_id).execute()

    return {"geloescht": True, "nachricht": "Termin wurde gelöscht."}