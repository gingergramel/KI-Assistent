import os
import time
from datetime import datetime

from dotenv import load_dotenv
from google import genai
from google.genai import types

import tools
from tools import (
    termine_abrufen,
    termin_anlegen,
    wetter_abrufen,
    news_abrufen,
    kalender_wurde_geaendert,
)

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(timeout=30000),  # Millisekunden
)

MODEL = "gemini-3.6-flash"

# Bei Überlastung (503) bis zu 3 Versuche, mit 2 s und 4 s Pause dazwischen
MAX_VERSUCHE = 3
WARTEZEIT_SEKUNDEN = 2

WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

WERKZEUGE = [termine_abrufen, termin_anlegen, wetter_abrufen, news_abrufen]

# Ein Gesprächsverlauf pro Browser-Sitzung (im Arbeitsspeicher, nach Neustart leer)
_sessions = {}


def _system_anweisung():
    jetzt = datetime.now()
    wochentag = WOCHENTAGE[jetzt.weekday()]

    return (
        "Du bist der persönliche Assistent des Nutzers. "
        "Antworte kurz und freundlich auf Deutsch, ohne Markdown-Formatierung "
        "(keine Sternchen, keine Überschriften).\n"
        f"Heute ist {wochentag}, der {jetzt:%d.%m.%Y} ({jetzt:%Y-%m-%d}), "
        f"es ist {jetzt:%H:%M} Uhr (Zeitzone Europa/Wien).\n"
        "Für Termine, Wetter und Nachrichten nutzt du immer die Werkzeuge und erfindest nie Daten. "
        "Bestätige angelegte Termine mit Titel, Datum und Uhrzeit."
    )


def _ist_ueberlastet(fehler) -> bool:
    """Erkennt, ob Gemini wegen Überlastung abgelehnt hat (503)."""
    text = str(fehler)
    return "503" in text or "UNAVAILABLE" in text


def ask_gemini(prompt: str):
    """Einfacher Testcall an Gemini."""
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )
    return response.text


def chat_mit_gemini(session_id: str, nachricht: str) -> dict:
    """Schickt eine Nachricht an Gemini. Gemini ruft bei Bedarf selbst die Werkzeuge auf."""
    chat = _sessions.get(session_id)

    if chat is None:
        chat = client.chats.create(
            model=MODEL,
            config=types.GenerateContentConfig(
                system_instruction=_system_anweisung(),
                tools=WERKZEUGE,
            ),
        )
        _sessions[session_id] = chat

    kalender_wurde_geaendert()  # Merker zurücksetzen

    antwort = None
    for versuch in range(MAX_VERSUCHE):
        try:
            antwort = chat.send_message(nachricht)
            break
        except Exception as fehler:
            letzter_versuch = versuch == MAX_VERSUCHE - 1
            termin_schon_angelegt = tools._kalender_geaendert

            if not _ist_ueberlastet(fehler) or letzter_versuch or termin_schon_angelegt:
                raise

            pause = WARTEZEIT_SEKUNDEN * (versuch + 1)
            print(f"Gemini überlastet, neuer Versuch in {pause} s ({versuch + 1}/{MAX_VERSUCHE})")
            time.sleep(pause)

    return {
        "antwort": antwort.text or "Dazu konnte ich leider keine Antwort erzeugen.",
        "kalender_geaendert": kalender_wurde_geaendert(),
    }