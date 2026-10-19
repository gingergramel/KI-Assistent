from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from calendar_service import get_upcoming_events, get_events_between, create_event
from news import get_top_news
from weather import get_weather_auto_json

VIENNA = ZoneInfo("Europe/Vienna")

# Merker, ob im aktuellen Chat ein Termin angelegt wurde (damit das Frontend die Kalenderansicht neu lädt)
_kalender_geaendert = False


def kalender_wurde_geaendert() -> bool:
    """Gibt zurück, ob seit dem letzten Aufruf ein Termin angelegt wurde, und setzt den Merker zurück."""
    global _kalender_geaendert
    geaendert = _kalender_geaendert
    _kalender_geaendert = False
    return geaendert


def _event_kurz(event):
    return {
        "titel": event.get("summary", "Ohne Titel"),
        "start": event["start"].get("dateTime", event["start"].get("date")),
        "ende": event["end"].get("dateTime", event["end"].get("date")),
    }


def _zeit_lokal(iso_text):
    """Wandelt eine Zeit von Google (UTC) in Wiener Zeit um."""
    zeit = datetime.fromisoformat(iso_text.replace("Z", "+00:00")).astimezone(VIENNA)
    return zeit.strftime("%Y-%m-%d %H:%M")


# ===== Werkzeuge, die Gemini selbst aufrufen darf =====
# Gemini liest den Funktionsnamen, die Beschreibung und die Parameter und entscheidet danach,
# wann es welches Werkzeug braucht.

def termine_abrufen(datum: str = "") -> dict:
    """Liest Termine aus dem Google-Kalender des Nutzers.

    Args:
        datum: Optional. Ein einzelner Tag im Format JJJJ-MM-TT. Ohne Angabe werden die nächsten Termine geliefert.
    """
    try:
        if datum:
            try:
                tag = datetime.strptime(datum, "%Y-%m-%d")
            except ValueError:
                return {"fehler": "Das Datum muss im Format JJJJ-MM-TT angegeben werden."}
            events = get_events_between(tag, tag + timedelta(days=1))
        else:
            events = get_upcoming_events(10)

        return {"termine": [_event_kurz(e) for e in events]}
    except Exception as fehler:
        print("Fehler beim Lesen des Kalenders:", fehler)
        return {"fehler": "Der Kalender konnte nicht gelesen werden."}


def termin_anlegen(titel: str, datum: str, uhrzeit: str, dauer_minuten: int = 60) -> dict:
    """Legt einen neuen Termin im Google-Kalender des Nutzers an. Ist der Zeitraum schon belegt, wird nichts angelegt und der Konflikt gemeldet.

    Args:
        titel: Titel des Termins.
        datum: Datum im Format JJJJ-MM-TT.
        uhrzeit: Startzeit im Format HH:MM (24 Stunden).
        dauer_minuten: Dauer in Minuten, Standard ist 60.
    """
    global _kalender_geaendert

    try:
        start = datetime.strptime(f"{datum} {uhrzeit}", "%Y-%m-%d %H:%M")
    except ValueError:
        return {"angelegt": False, "fehler": "Datum oder Uhrzeit haben ein ungültiges Format."}

    try:
        ergebnis = create_event(titel, start, int(dauer_minuten))
    except Exception as fehler:
        print("Fehler beim Anlegen des Termins:", fehler)
        return {"angelegt": False, "fehler": "Der Termin konnte nicht angelegt werden."}

    if not ergebnis.get("erstellt"):
        belegt = []
        for zeitraum in ergebnis.get("konflikte", []):
            belegt.append({
                "von": _zeit_lokal(zeitraum["start"]),
                "bis": _zeit_lokal(zeitraum["end"]),
            })
        return {
            "angelegt": False,
            "konflikt": True,
            "belegt": belegt,
            "hinweis": "Der Zeitraum ist schon belegt, es wurde nichts angelegt.",
        }

    erstellt = ergebnis["termin"]
    _kalender_geaendert = True
    return {
        "angelegt": True,
        "titel": erstellt.get("summary"),
        "start": erstellt["start"].get("dateTime"),
    }


def wetter_abrufen() -> dict:
    """Liefert den heutigen Wetterverlauf in 3-Stunden-Schritten (Temperatur, Beschreibung, Regenwahrscheinlichkeit)."""
    try:
        return get_weather_auto_json()
    except Exception as fehler:
        print("Fehler beim Wetter:", fehler)
        return {"fehler": "Das Wetter konnte nicht abgerufen werden."}


def news_abrufen(thema: str = "Österreich") -> dict:
    """Liefert aktuelle Nachrichten zu einem Thema.

    Args:
        thema: Suchbegriff, zum Beispiel "Österreich" oder "Sport".
    """
    try:
        return get_top_news(thema, 5)
    except Exception as fehler:
        print("Fehler bei den News:", fehler)
        return {"fehler": "Die News konnten nicht abgerufen werden."}