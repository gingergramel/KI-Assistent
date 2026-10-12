import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-3.6-flash"

SYSTEM_ANWEISUNG = (
    "Du bist der persönliche Assistent des Nutzers. "
    "Antworte kurz und freundlich auf Deutsch, ohne Markdown-Formatierung "
    "(keine Sternchen, keine Überschriften)."
)

# Ein Gesprächsverlauf pro Browser-Sitzung (im Arbeitsspeicher, nach Neustart leer)
_sessions = {}


def ask_gemini(prompt: str):
    """Einfacher Testcall an Gemini."""
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )
    return response.text


def chat_mit_gemini(session_id: str, nachricht: str) -> str:
    """Schickt eine Nachricht an Gemini und merkt sich den Verlauf der Sitzung."""
    chat = _sessions.get(session_id)

    if chat is None:
        chat = client.chats.create(
            model=MODEL,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_ANWEISUNG),
        )
        _sessions[session_id] = chat

    antwort = chat.send_message(nachricht)
    return antwort.text or "Dazu konnte ich leider keine Antwort erzeugen."