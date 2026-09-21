# KI-Assistent

Sprachgesteuerter persönlicher Assistent mit Kalender-, Mail-, Wetter- und News-Anbindung, Gedächtnis, Aufgabenverwaltung und proaktiven Erinnerungen — als Web-App für Desktop & Mobil.

Schulprojekt zu zweit, 26 Wochen Zeitbudget.

## Projektziel

Ein persönlicher, sprachgesteuerter KI-Assistent, der ein tägliches gesprochenes Briefing gibt (Termine, E-Mails, Wetter, Nachrichten), Terminplanung und Aufgabenverwaltung per natürlicher Sprache übernimmt, proaktiv an Termine/Aufgaben erinnert und sich dauerhaft Vorlieben, Fakten und Gewohnheiten merkt.

## Architektur

**Tech-Stack:**
- **Backend:** FastAPI (Python) — orchestriert LLM-Anfragen und externe APIs
- **LLM:** Google Gemini API (`gemini-2.0-flash`) — Function-Calling-fähig, kostenloses Kontingent
- **Externe APIs:** OpenWeatherMap (Wetter), Google Calendar/Gmail API (geplant), News-API (geplant)
- **Frontend:** Reines HTML/CSS/JavaScript — kein Framework, nutzt die native Web Speech API des Browsers
- **Datenbank:** SQLite (geplant, für Gedächtnis-Funktion)
- **Kommunikation:** Frontend ↔ Backend per REST (JSON/Text über `fetch()`)

**Ordnerstruktur:**
KI-Assistent/
├── backend/
│ ├── main.py # FastAPI-Endpoints
│ ├── weather.py # Wetter-Logik
│ ├── llm.py # Gemini-Anbindung
│ ├── requirements.txt
│ └── .env # API-Keys (nicht im Repo)
├── frontend/
│ ├── index.html
│ ├── css/style.css
│ ├── js/
│ │ ├── geolocation.js
│ │ ├── weather.js
│ │ ├── chat.js
│ │ └── main.js
│ └── assets/icons/
├── start.ps1 # Startet Backend + Frontend zusammen
├── .gitignore
└── README.md

## Setup

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Eigene `.env` im `backend`-Ordner anlegen:

GEMINI_API_KEY=dein_key
OPENWEATHER_API_KEY=dein_key


**Starten (Backend + Frontend zusammen):**
```powershell
.\start.ps1
```

Öffnet automatisch `http://localhost:5500` im Browser.

## Status

Aktueller Stand: Kern-MVP in Arbeit — Wetter-Anbindung funktioniert, Gemini-API-Anbindung funktioniert, Kalender/Mail/News folgen.