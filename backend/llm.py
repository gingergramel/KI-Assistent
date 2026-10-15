import os
from datetime import datetime

from dotenv import load_dotenv
from google import genai
from google.genai import types

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
    antwort = chat.send_message(nachricht)

    return {
        "antwort": antwort.text or "Dazu konnte ich leider keine Antwort erzeugen.",
        "kalender_geaendert": kalender_wurde_geaendert(),
    }