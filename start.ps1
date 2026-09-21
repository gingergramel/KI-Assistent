# Backend starten (in neuem Fenster)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; venv\Scripts\activate; uvicorn main:app --reload"

# Kurz warten, damit das Backend hochfahren kann
Start-Sleep -Seconds 2

# Frontend starten (einfacher Python-Webserver, in neuem Fenster)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; python -m http.server 5500"

# Browser automatisch öffnen
Start-Sleep -Seconds 1
Start-Process "http://localhost:5500"