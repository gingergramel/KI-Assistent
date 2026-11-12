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


def _auf_wien(dt):
    """Zeiten ohne Zeitzone gelten als Wiener Zeit, andere werden nach Wien umgerechnet."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=VIENNA)
    return dt.astimezone(VIENNA)


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


# ===== Pro Tag darf ein Terminname nur einmal vorkommen =====

def _normalisiert(text):
    """Vergleicht Namen ohne Rücksicht auf Groß-/Kleinschreibung und überflüssige Leerzeichen."""
    return " ".join((text or "").split()).casefold()


def _termine_am_tag(service, tag):
    """Alle Termine mit Uhrzeit, die an diesem Kalendertag (Wiener Zeit) beginnen."""
    tag_start = datetime(tag.year, tag.month, tag.day, tzinfo=VIENNA)
    tag_ende = tag_start + timedelta(days=1)

    items = service.events().list(
        calendarId="primary",
        timeMin=tag_start.isoformat(),
        timeMax=tag_ende.isoformat(),
        singleEvents=True,
        orderBy="startTime"
    ).execute().get("items", [])

    ergebnis = []
    for e in items:
        if "dateTime" not in e["start"]:
            continue  # ganztägige Einträge zählen hier nicht
        beginn = _auf_wien(datetime.fromisoformat(e["start"]["dateTime"]))
        if beginn.date() == tag:
            ergebnis.append(e)

    return ergebnis


def _finde_gleichen_namen(service, titel, tag, ausser_id=None):
    """Sucht an diesem Tag einen Termin mit demselben Namen. Gibt ihn zurück oder None."""
    gesucht = _normalisiert(titel)

    for e in _termine_am_tag(service, tag):
        if ausser_id and e["id"] == ausser_id:
            continue
        if _normalisiert(e.get("summary")) == gesucht:
            return e

    return None


def create_event(titel, start_datetime, dauer_minuten=60):
    """Legt einen Termin an. Pro Tag darf ein Terminname nur einmal vorkommen:
    Gibt es am selben Tag schon einen Termin mit diesem Namen, wird er stattdessen
    auf die neue Zeit verschoben. Sonst wird nur angelegt, wenn der Zeitraum frei ist."""

    if dauer_minuten <= 0:
        raise ValueError("Die Dauer muss größer als 0 sein.")

    start = _auf_wien(start_datetime)
    ende = start + timedelta(minutes=dauer_minuten)

    service = get_calendar_service()
    vorhanden = _finde_gleichen_namen(service, titel, start.date())

    if vorhanden is not None:
        name = vorhanden.get("summary", titel)
        alter_start = _auf_wien(datetime.fromisoformat(vorhanden["start"]["dateTime"]))
        altes_ende = _auf_wien(datetime.fromisoformat(vorhanden["end"]["dateTime"]))

        if alter_start == start and altes_ende == ende:
            return {
                "erstellt": False,
                "aktualisiert": False,
                "nachricht": f"Der Termin „{name}“ steht an diesem Tag schon genau so im Kalender.",
                "konflikte": []
            }

        ergebnis = update_event(
            vorhanden["id"],
            start_datetime=start,
            dauer_minuten=dauer_minuten
        )

        if not ergebnis.get("geaendert"):
            return {
                "erstellt": False,
                "aktualisiert": False,
                "nachricht": (
                    f"Den Termin „{name}“ gibt es an diesem Tag schon, er wurde aber nicht verschoben. "
                    + ergebnis.get("nachricht", "")
                ),
                "konflikte": ergebnis.get("konflikte", [])
            }

        return {
            "erstellt": True,
            "aktualisiert": True,
            "nachricht": f"Den Termin „{name}“ gab es an diesem Tag schon, er wurde auf die neue Zeit verschoben.",
            "termin": ergebnis["termin"]
        }

    # Kein Termin mit diesem Namen an diesem Tag: neu anlegen, wenn der Zeitraum frei ist
    pruefung = check_calendar_availability(
        start,
        dauer_minuten
    )

    if not pruefung["verfuegbar"]:
        return {
            "erstellt": False,
            "aktualisiert": False,
            "nachricht": "Termin konnte nicht erstellt werden. Zeitraum belegt.",
            "konflikte": pruefung["konflikte"]
        }

    neuer_start = datetime.fromisoformat(pruefung["start"])
    neues_ende = datetime.fromisoformat(pruefung["ende"])

    event = {
        "summary": titel,
        "start": {
            "dateTime": neuer_start.isoformat(),
            "timeZone": "Europe/Vienna"
        },
        "end": {
            "dateTime": neues_ende.isoformat(),
            "timeZone": "Europe/Vienna"
        }
    }

    erstelltes_event = service.events().insert(
        calendarId="primary",
        body=event
    ).execute()

    return {
        "erstellt": True,
        "aktualisiert": False,
        "nachricht": "Termin wurde erfolgreich erstellt.",
        "termin": erstelltes_event
    }


def update_event(event_id, titel=None, start_datetime=None, dauer_minuten=None):
    """Ändert Titel, Startzeit und/oder Dauer eines Termins.
    Der Name darf an dem Tag nur einmal vorkommen, und bei einer neuen Zeit wird auf Konflikte geprüft.
    Der Termin selbst zählt dabei nicht als Konflikt."""

    service = get_calendar_service()
    event = service.events().get(calendarId="primary", eventId=event_id).execute()

    aenderungen = {}
    neuer_titel = event.get("summary", "")

    if titel is not None and titel.strip():
        neuer_titel = titel.strip()
        aenderungen["summary"] = neuer_titel

    zeit_aendern = start_datetime is not None or dauer_minuten is not None

    ziel_tag = None
    if "dateTime" in event["start"]:
        ziel_tag = _auf_wien(datetime.fromisoformat(event["start"]["dateTime"])).date()

    neuer_start = None
    neues_ende = None

    if zeit_aendern:
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
        ziel_tag = neuer_start.date()

    # Pro Tag darf ein Name nur einmal vorkommen
    if ziel_tag is not None and (aenderungen or zeit_aendern):
        doppelt = _finde_gleichen_namen(service, neuer_titel, ziel_tag, ausser_id=event_id)

        if doppelt is not None:
            return {
                "geaendert": False,
                "nachricht": (
                    f"Am {ziel_tag:%d.%m.%Y} gibt es schon einen Termin „{neuer_titel}“. "
                    "Pro Tag darf ein Name nur einmal vorkommen."
                )
            }

    if zeit_aendern:
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