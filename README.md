# 🏠 Smart Home Hub

Ein einfaches, aber leistungsstarkes Smart-Home-Backend mit Geräteverwaltung, Benutzerverwaltung und Tages-Simulation.

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57.svg)](https://www.sqlite.org/)

---

## ✨ Features

- 💡 **Lampen-Steuerung** – Ein-/Ausschalten mit Helligkeitsregelung
- ⏰ **Wecker-Verwaltung** – Erstellen und Verwalten von Alarmen
- 🌡️ **Thermostat-Logik** – Temperatur-abhängige Steuerung
- 🌅 **Tages-Simulation** – Automatischer Day-Emulator für realistische Szenarien
- 🏠 **Raum-Verwaltung** – Geräte in verschiedenen Räumen organisieren
- 👤 **Benutzerverwaltung** – Session-basierte Authentifizierung
- 🗄️ **Persistente Speicherung** – SQLite-Datenbank für alle Daten
- 🚀 **REST API** – Moderne API mit FastAPI

---

## 🛠️ Verwendete Technologien

- **Python 3.x**
- **FastAPI** – Hochperformantes Web-Framework
- **SQLite** – Leichtgewichtige Datenbank
- **Starlette Sessions** – Session-Management

---

## 🚀 Installation

### Voraussetzungen

- Python 3.8 oder höher
- pip

### Schritt-für-Schritt

1. **Repository klonen**
   ```bash
   git clone https://github.com/Kyyuu133/smarthome-Hub.git
   cd smarthome-Hub
   ```

2. **Virtuelle Umgebung erstellen (empfohlen)**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **Abhängigkeiten installieren**
   ```bash
   pip install -r requirements.txt
   ```

4. **Anwendung starten**
   ```bash
   uvicorn main:app --reload
   ```

5. **API-Dokumentation öffnen**  
   Nach dem Start ist die interaktive API-Dokumentation verfügbar unter:
   - 📚 Swagger UI: http://localhost:8000/docs
   - 📘 ReDoc: http://localhost:8000/redoc

---

## 📡 API-Endpunkte

### Authentifizierung

| Methode | Endpunkt | Beschreibung |
|---|---|---|
| `POST` | `/login` | Benutzeranmeldung |
| `POST` | `/logout` | Benutzerabmeldung |
| `GET` | `/me` | Aktuellen Benutzer abrufen |

### Geräte-Verwaltung

| Methode | Endpunkt | Beschreibung |
|---|---|---|
| `GET` | `/devices` | Alle Geräte auflisten |
| `GET` | `/devices/{id}` | Einzelnes Gerät abrufen |
| `POST` | `/devices` | Neues Gerät erstellen |
| `PUT` | `/devices/{id}` | Gerät aktualisieren |
| `DELETE` | `/devices/{id}` | Gerät löschen |
| `POST` | `/devices/{id}/toggle` | Gerät ein-/ausschalten |

### Räume

| Methode | Endpunkt | Beschreibung |
|---|---|---|
| `GET` | `/rooms` | Alle Räume auflisten |
| `POST` | `/rooms` | Neuen Raum erstellen |

### Tages-Simulation

| Methode | Endpunkt | Beschreibung |
|---|---|---|
| `GET` | `/day/status` | Aktuellen Tagesstatus abrufen |
| `POST` | `/day/emulate` | Tagesverlauf simulieren |
| `POST` | `/day/set-time` | Zeit manuell setzen |

---

## 💾 Datenbank-Schema

Das System verwendet SQLite mit folgenden Haupttabellen:

- **users** – Benutzerkonten und Sessions
- **devices** – Smart-Home-Geräte (Lampen, Thermostate, Wecker)
- **rooms** – Raum-Zuordnungen
- **schedules** – Zeitpläne und Automationen
- **day_states** – Tages-Simulationszustände

---

## 🎯 Verwendungsbeispiele

**Nutzer Anlegen**

![[Create New Account.png]]

**Raum erstellen**

![[Create Room.png]]

**Raum verwalten**

![[Manage Existing Room.png]]

**Devices erstellen** 

![[Add Device for Room.png]]

**Rule setzen**

![[Adjust Rule for specific device.png]]

**Rules für ein Spezifisches Device**

![[Adjust Rule for specific device.png]]

**Device Event Log History für ein Device**

![[device event log history for device.png]]

**Device Event Log History für alle Devices**

![[device event log history for all.png]]

**Aktueller Status aller Devices**

![[Current States all Devices.png]]

---

## 📂 Projektstruktur

```
smarthome-Hub/
├── backend/
│   ├── database.py                  # Datenbank-Verbindung
│   ├── day_emulator_dimmable.py     # Tages-Simulation mit Dimmer-Unterstützung
│   ├── device.py                    # Geräte-Logik
│   ├── devicetest.py                # Geräte-Tests
│   ├── emulator.py                  # Basis-Emulator
│   ├── hub.db                       # SQLite-Datenbank
│   ├── hub.sql                      # SQL-Schema
│   ├── login.py                     # Login & Session
│   ├── main.py                      # Einstiegspunkt (FastAPI App)
│   ├── main_2.py                    # Alternativer Einstiegspunkt
│   ├── migrate_rooms_users.py       # DB-Migration
│   ├── requirements.txt             # Python-Abhängigkeiten
│   ├── rooms.py                     # Raum-Logik
│   ├── rooms_devices_api.py         # Räume & Geräte API
│   ├── rules_api.py                 # Regelwerk API
│   ├── status_api.py                # Status API
│   ├── users_api.py                 # Benutzerverwaltung API
│   └── templates/                   # HTML-Templates (Jinja2)
│       ├── dashboard.html
│       ├── login.html
│       ├── setup.html
│       ├── devices/
│       │   ├── add.html
│       │   └── list.html
│       ├── rooms/
│       │   ├── create.html
│       │   └── list.html
│       ├── rules/
│       │   ├── create.html
│       │   ├── device.html
│       │   ├── edit.html
│       │   ├── list.html
│       │   └── room.html
│       └── status/
│           ├── all/
│           │   └── devices.html
│           └── events/
│               ├── device_history.html
│               ├── history.html
│               ├── overview.html
│               └── room.html
├── frontend/
├── Test_Simulation_Niki/
├── login.py
├── hub.db
├── log.txt
└── README.md
```

---

## 👤 Autoren

**Kyyuu133**  
GitHub: 
- [@Kyyuu133](https://github.com/Kyyuu133)
- [@hayalet94](https://github.com/hayalet94)
- [@NvK-Bit](https://github.com/NvK-Bit)
- [@DevDaio](https://github.com/DevDaio)

---

## 🙏 Danksagung

- [FastAPI](https://fastapi.tiangolo.com/) – Web-Framework für die REST API (APIRouter, Request, Form, Response)
- [Starlette](https://www.starlette.io/) – ASGI-Basis von FastAPI, inkl. Session-Middleware
- [Pydantic](https://docs.pydantic.dev/) – Datenvalidierung und Modelle (BaseModel)
- [Jinja2](https://jinja.palletsprojects.com/) – HTML-Template-Engine für das Web-Interface
- [SQLite3](https://www.sqlite.org/) – Eingebettete, dateibasierte Datenbank
- [Uvicorn](https://www.uvicorn.org/) – ASGI-Server zum Ausführen der FastAPI-App
- [itsdangerous](https://itsdangerous.palletsprojects.com/) – Sichere Session-Signierung
- Die Open-Source-Community für die tollen Tools
