"""Vorab-Check für die Demo.

Aufruf im Projektordner, bei laufenden Servern (start.bat):
    python vorab_check.py            prüft alles ohne Gemini
    python vorab_check.py --gemini   prüft zusätzlich Gemini (verbraucht 1 Anfrage)
"""
import os
import posixpath
import re
import sys

import requests
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")
FRONTEND = os.path.join(ROOT, "frontend")
BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:5500"

MIT_GEMINI = "--gemini" in sys.argv
probleme = 0


def ok(text):
    print(f"  [ OK ]   {text}")


def warnung(text):
    print(f"  [WARN]   {text}")


def fehler(text):
    global probleme
    probleme += 1
    print(f"  [FEHLER] {text}")


def titel(text):
    print(f"\n{text}")


def hole(url, timeout):
    """Gibt (Antwort, None) zurück, oder (None, Fehlertext)."""
    try:
        return requests.get(url, timeout=timeout), None
    except requests.exceptions.ConnectionError:
        return None, "nicht erreichbar"
    except requests.exceptions.Timeout:
        return None, f"keine Antwort nach {timeout} Sekunden"
    except requests.exceptions.RequestException as e:
        return None, str(e)


def pruefe_endpoint(name, pfad, timeout, schluessel, hinweis=""):
    antwort, fehler_text = hole(BACKEND_URL + pfad, timeout)

    if fehler_text:
        fehler(f"{name}: {fehler_text}. {hinweis}")
        return

    if antwort.status_code != 200:
        fehler(f"{name}: Status {antwort.status_code}. {hinweis}")
        return

    if schluessel:
        try:
            daten = antwort.json()
        except ValueError:
            fehler(f"{name}: Antwort ist kein JSON")
            return

        if isinstance(daten, dict) and "error" in daten:
            fehler(f"{name}: {daten['error']}")
            return

        if isinstance(daten, dict) and schluessel not in daten:
            fehler(f"{name}: Feld '{schluessel}' fehlt in der Antwort")
            return

    ok(name)


# ===== 1. Rechner und Dateien =====
titel("1. Rechner und Dateien")

if sys.version_info >= (3, 10):
    ok(f"Python {sys.version_info.major}.{sys.version_info.minor}")
else:
    fehler("Python 3.10 oder neuer wird gebraucht")

try:
    from zoneinfo import ZoneInfo

    ZoneInfo("Europe/Vienna")
    ok("Zeitzonen-Daten für Europe/Vienna vorhanden")
except Exception:
    fehler("Zeitzonen-Daten fehlen. Abhilfe: pip install tzdata")

load_dotenv(os.path.join(BACKEND, ".env"))
for name in ("GEMINI_API_KEY", "OPENWEATHER_API_KEY", "NEWS_API_KEY"):
    if os.getenv(name):
        ok(f"{name} ist in backend/.env gesetzt")
    else:
        fehler(f"{name} fehlt in backend/.env")

if os.path.exists(os.path.join(BACKEND, "credentials.json")):
    ok("backend/credentials.json vorhanden")
else:
    fehler("backend/credentials.json fehlt (Google-Zugang)")

if os.path.exists(os.path.join(BACKEND, "token.json")):
    ok("backend/token.json vorhanden (Google-Login ist gespeichert)")
else:
    warnung("backend/token.json fehlt: Beim ersten Abruf öffnet sich ein Google-Login im Browser")


# ===== 2. Backend =====
titel("2. Backend (Port 8000)")

antwort, fehler_text = hole(BACKEND_URL + "/openapi.json", 10)

if fehler_text:
    fehler(f"Backend {fehler_text}. Ist start.bat gestartet?")
else:
    try:
        routen = antwort.json().get("paths", {})
    except ValueError:
        routen = {}
        fehler("Auf Port 8000 läuft kein FastAPI-Backend")

    for route in ("/chat", "/kalender", "/kalender/termin", "/kalender/termin/{event_id}"):
        if route in routen:
            ok(f"Route {route}")
        else:
            fehler(f"Route {route} fehlt. Es läuft ein alter Stand des Backends, start.bat neu starten")

    pruefe_endpoint(
        "Kalender lesen", "/kalender", 60, "termine",
        "Ist der Google-Login abgelaufen? Dann backend/token.json löschen und neu anmelden."
    )
    pruefe_endpoint("Wetter", "/wetter/auto/json", 20, "verlauf", "Ist der OpenWeatherMap-Key aktiv?")
    pruefe_endpoint("News", "/news", 20, "artikel", "Ist das NewsAPI-Tageslimit erreicht?")
    pruefe_endpoint(
        "Mails", "/api/mails", 60, None,
        "Ist der Google-Login abgelaufen? Dann backend/token.json löschen und neu anmelden."
    )

    if MIT_GEMINI:
        pruefe_endpoint(
            "Gemini", "/llm-test", 45, "antwort",
            "503 heißt: Google überlastet, 429: Tageslimit erreicht."
        )
    else:
        warnung("Gemini nicht getestet (mit --gemini, verbraucht eine Anfrage)")


# ===== 3. Frontend =====
titel("3. Frontend (Port 5500)")

antwort, fehler_text = hole(FRONTEND_URL + "/index.html", 10)

if fehler_text:
    fehler(f"Frontend {fehler_text}. Ist start.bat gestartet?")
else:
    dateien = {"index.html"}

    for pfad in re.findall(r'(?:src|href)="([^"#]+)"', antwort.text):
        if not pfad.startswith(("http://", "https://", "//")):
            dateien.add(pfad)

    # Bilder, die nur im CSS stehen (zum Beispiel die Wetter-Hintergründe)
    for css in [p for p in dateien if p.endswith(".css")]:
        css_antwort, css_fehler = hole(FRONTEND_URL + "/" + css, 10)
        if css_fehler or css_antwort.status_code != 200:
            continue
        for url in re.findall(r'url\(["\']?([^"\')]+)["\']?\)', css_antwort.text):
            if url.startswith(("http", "data:")):
                continue
            dateien.add(posixpath.normpath(posixpath.join(posixpath.dirname(css), url)))

    in_ordnung = 0

    for pfad in sorted(dateien):
        datei_antwort, datei_fehler = hole(FRONTEND_URL + "/" + pfad, 10)

        if datei_fehler or datei_antwort.status_code != 200:
            fehler(f"{pfad} lässt sich nicht laden (fehlt die Datei oder liegt sie im falschen Ordner?)")
            continue

        lokal = os.path.join(FRONTEND, *pfad.split("/"))
        if pfad.endswith((".html", ".js", ".css")) and os.path.exists(lokal):
            with open(lokal, "rb") as datei:
                if datei.read() != datei_antwort.content:
                    fehler(f"{pfad}: Der Server liefert eine ANDERE Version aus als die Datei im Projektordner")
                    continue

        in_ordnung += 1

    ok(f"{in_ordnung} von {len(dateien)} Dateien laden und entsprechen dem Projektordner")


# ===== Ergebnis =====
print()
if probleme == 0:
    print("Alles bereit für die Demo.")
else:
    print(f"{probleme} Problem(e) gefunden. Bitte vor der Demo beheben.")

sys.exit(1 if probleme else 0)