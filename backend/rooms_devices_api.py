from fastapi import FastAPI, Request, Form, Response              # FastAPI für Web-API
from fastapi.responses import HTMLResponse, RedirectResponse      # HTML-Response und Umleitung
from fastapi.templating import Jinja2Templates                    # Template-Engine
from pydantic import BaseModel                                    # Datenvalidierung
from login import username_check, password_check                  # Login-Funktionen
from typing import Optional                                       # Typ-Hinweise
from starlette.middleware.sessions import SessionMiddleware       # Session-Management
import sqlite3                                                    # Datenbankanbindung
import os                                                         # Betriebssystem-Funktionen
from users_api import get_db, get_current_user                    # Benutzer-API-Funktionen
from rooms import Room                                            # Room-Klasse
from main import Database                                         # Datenbank-Wrapper-Klasse

# HAUPTANWENDUNG SETUP

app = FastAPI()                                                   # FastAPI-Anwendung erstellen
app.add_middleware(SessionMiddleware, secret_key="SUPER_SECRET_KEY_123")  # Session-Middleware hinzufügen

# Pfade für Templates und Datenbank
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

db_path = os.path.join(BASE_DIR, "hub.db")
db = Database(db_path)                                            # Datenbank-Instanz erstellen                        


# HILFSFUNKTION: Aktuellen Raum aus Session holen
def current_room(request: Request):
    """
    Gibt den aktuellen Raum aus der Session zurück oder None.
    
    WICHTIG - Zugriffsregeln (Sicherheit!):
        • admin  → darf ALLE räume sehen und bearbeiten
        • user   → darf nur EIGENE räume (die er erstellt hat) sehen und bearbeiten
    """
    # Raum-ID aus der Browser-Session holen
    room_id = request.session.get("room_id")
    # Benutzer-ID aus der Browser-Session holen
    user_id = request.session.get("user_id")
    # Benutzer-Rolle aus der Browser-Session holen ("admin" oder "user")
    user_role = request.session.get("user_role")

    # Wenn keine Raum-ID in Session → abbrechen
    if room_id is None:
        return None

    # Verbindung zur Datenbank öffnen
    conn, curs = get_db()

    # ADMIN: Darf jeden Raum sehen (nur room_id prüfen)
    if user_role == "admin":
        room = curs.execute("""
            SELECT room_id, room_name, user_id 
            FROM rooms 
            WHERE room_id = ?
        """, (room_id,)).fetchone()

    # NORMALER USER: Darf nur seine eigenen Räume sehen (room_id UND user_id müssen passen)
    else:
        room = curs.execute("""
            SELECT room_id, room_name, user_id 
            FROM rooms 
            WHERE room_id = ? 
            AND user_id = ?;
        """, (room_id, user_id)).fetchone()

    # Datenbankverbindung schließen
    conn.close()

    # Wenn Raum nicht existiert → Session bereinigen und None zurückgeben
    if room is None:
        request.session.pop("room_id", None)
        return None

    # Raum-Daten zurückgeben
    return room
    
    
# GET /rooms → Überprüft, ob Räume vorhanden sind
@app.get("/rooms", response_class=HTMLResponse)
async def rooms_page(request: Request):
    """
    Startseite für Raumverwaltung:
    - Wenn KEINE Räume vorhanden: Zeige Formular zum Raum erstellen
    - Wenn Räume vorhanden: Leite zur Raum-Liste weiter
    """
    # Verbindung zur Datenbank öffnen
    conn, curs = get_db()

    try:
        # Zähle, wie viele Räume in der Datenbank existieren
        curs.execute("SELECT COUNT(*) FROM rooms")
        rooms_count = curs.fetchone()[0]
    except sqlite3.OperationalError:
        # Falls Tabelle noch nicht existiert → 0 Räume
        rooms_count = 0

    # Datenbankverbindung schließen
    conn.close()

    # KEINE Räume vorhanden → Formular zum Erstellen zeigen
    if rooms_count == 0:
        return templates.TemplateResponse("rooms/create.html", {"request": request})

    # RÄUME vorhanden → Leite zur Raum-Liste weiter
    return RedirectResponse(url="/rooms/list", status_code=302)


# GET /rooms/list → Zeigt Liste aller verfügbaren Räume
@app.get("/rooms/list", response_class=HTMLResponse)
async def show_rooms_page(request: Request):
    """
    Zeigt alle Räume aus der Datenbank in einer HTML-Liste.
    """
    # Verbindung zur Datenbank öffnen
    conn, curs = get_db()
    # Hole alle Räume aus der Datenbank
    rooms = curs.execute("SELECT * FROM rooms").fetchall()
    # Datenbankverbindung schließen
    conn.close()

    # Gebe die Raumliste im HTML-Template aus
    return templates.TemplateResponse("rooms/list.html", {
        "request": request,
        "rooms": rooms
    })

# POST /rooms/create → Erstellt einen neuen Raum

@app.post("/rooms/create", response_class=HTMLResponse)
async def create_room(
    request: Request,
    room_name: str = Form(...)          
):
    """
    Erstellt einen neuen Raum:
    1. Prüft, ob Raumname bereits existiert
    2. Erstellt neuen Raum mit Benutzer-ID
    3. Leitet zur Raum-Liste weiter
    """
    # Verbindung zur Datenbank öffnen
    conn, curs = get_db()

    # SICHERHEIT: Prüfe, ob dieser Raumname bereits existiert
    existing = curs.execute(
        "SELECT * FROM rooms WHERE room_name = ?", (room_name,)
    ).fetchone()
    conn.close()
    
    # FEHLERFALL: Raumname existiert bereits → Fehler anzeigen
    if existing:
        return templates.TemplateResponse("rooms/add.html", {
            "request": request,
            "error": f"Raum '{room_name}' existiert bereits"
        })

    # Neues Room-Objekt erstellen
    room = Room(
        room_id=None,                                   # ID wird automatisch generiert
        room_name=room_name,                            # Name aus Formular
        user_id=request.session.get("user_id"),         # Benutzer-ID aus Session
        database=db                                     # Datenbank-Verbindung
    )
    # Raum in Datenbank speichern
    room.save_to_db()

    # ERFOLG: Leite zur Raum-Liste weiter
    return RedirectResponse(url="/rooms/list", status_code=302)



# POST /rooms/delete → Löscht einen vorhandenen Raum

@app.post("/rooms/delete", response_class=HTMLResponse)
async def delete_room(
    request: Request,
    room_id: int = Form(...),           
    room_name: str = Form(...)          
):
    """
    Löscht einen Raum und alle seine Geräte aus der Datenbank.
    """
    # SICHERHEIT: Prüfe, ob Raum-ID vorhanden ist
    if not room_id:
        return templates.TemplateResponse("rooms/list.html", {
            "request": request,
            "error": "Keine Raum-ID angegeben"
        })

    # Neues Room-Objekt erstellen mit den Raum-Daten
    room = Room(
        room_id=room_id,                                # Zu löschende Raum-ID
        room_name=room_name,                            # Name (für Info)
        user_id=request.session.get("user_id"),         # Benutzer-ID aus Session
        database=db                                     # Datenbank-Verbindung
    )
    # Raum aus Datenbank löschen
    room.delete_from_db()

    # ERFOLG: Leite zurück zur Raum-Liste weiter
    return RedirectResponse(url="/rooms/list", status_code=302)

# PUT /rooms/rename → Benennt einen vorhandenen Raum um
@app.put("/rooms/rename", response_class=HTMLResponse)
async def rename_room(
    request: Request,
    room_id: int = Form(...),           
    new_name: str = Form(...)           
):
    """
    Ändert den Namen eines vorhandenen Raums.
    """
    # SICHERHEIT: Prüfe, ob Raum-ID und neuer Name vorhanden sind
    if not room_id or not new_name:
        return templates.TemplateResponse("rooms/list.html", {
            "request": request,
            "error": "Keine Raum-ID oder neuer Name angegeben"
        })


#Devices

# ── GET /devices ── prüfen ob geräte vorhanden ────────────────────
@app.get("/devices", response_class=HTMLResponse)
async def devices_page(request: Request):
    room = current_room(request)
    if room is None:
        return RedirectResponse(url="/rooms", status_code=302)

    conn, curs = get_db()

    try:
        curs.execute("SELECT COUNT(*) FROM devices WHERE room_id = ?", (room["room_id"],))
        devices_count = curs.fetchone()[0]
    except sqlite3.OperationalError:
        devices_count = 0

    conn.close()

    # keine geräte → formular anzeigen
    if devices_count == 0:
        return templates.TemplateResponse("devices/add.html", {
            "request": request,
            "room": room
        })

    # geräte vorhanden → zur liste
    return RedirectResponse(url="/devices/list", status_code=302)



@app.get("/devices/list/room", response_class=HTMLResponse)
async def show_devices(request: Request):
    room = current_room(request)
    if room is None:
        return RedirectResponse(url="/rooms", status_code=302)

    conn, curs = get_db()

    devices = curs.execute("""
        SELECT device_id, device_name, device_type, status
        FROM devices
        WHERE room_id = ?
    """, (room["room_id"],)).fetchall()

    conn.close()

    return templates.TemplateResponse("devices/list.html", {
        "request": request,
        "devices": devices,
        "room": room
    })

@app.get("/devices/list/all", response_class=HTMLResponse)
async def show_all_devices(request: Request):
    conn, curs = get_db()
    devices = curs.execute("""
       SELECT * FROM devices
       """).fetchall()
    conn.close()
    return templates.TemplateResponse("devices/list_all.html", {
        "request": request,
        "devices": devices
        })

@app.post("/devices/create", response_class=HTMLResponse)
async def create_device( request: Request, device_name: str = Form(...), device_type: str = Form(...), device_id: int = Form(...)):
    room = current_room(request)
    if room is None:
        return RedirectResponse(url="/rooms", status_code=302)

    conn, curs = get_db()

    # prüfen ob gerät bereits existiert
    existing = curs.execute(
        "SELECT * FROM devices WHERE device_name = ? AND device_id = ?", (device_name, device_id)
    ).fetchone()

    if existing:
        conn.close()
        return templates.TemplateResponse("devices/add.html", {
            "request": request,
            "room": room,
            "error": f"Gerät '{device_name}' existiert bereits"
        })

    # room_id kommt aus session, nicht aus dem formular
    curs.execute("""
        INSERT INTO devices (room_id, device_name, device_type, status)
        VALUES (?, ?, ?, 0)
    """, (room["room_id"], device_name, device_type))

    conn.commit()
    conn.close()

    return RedirectResponse(url="/devices/list", status_code=302)


# ── POST /devices/delete ── gerät löschen ─────────────────────────
@app.post("/devices/delete", response_class=HTMLResponse)
async def delete_device(
    request: Request,
    device_id: int = Form(...)          # <input type="hidden" name="device_id">
):
    room = current_room(request)
    if room is None:
        return RedirectResponse(url="/rooms", status_code=302)

    conn, curs = get_db()

    # sicherheit: nur geräte löschen die auch wirklich in diesem raum sind
    curs.execute("""
        DELETE FROM devices 
        WHERE device_id = ? 
        AND room_id = ?
    """, (device_id, room["room_id"]))

    conn.commit()
    conn.close()

    return RedirectResponse(url="/devices/list", status_code=302)


# ── POST /devices/status ── gerät an/aus schalten ─────────────────
@app.post("/devices/status", response_class=HTMLResponse)
async def toggle_device_status(
    request: Request,
    device_id: int = Form(...),         # <input type="hidden" name="device_id">
    status: int = Form(...)             # <input type="hidden" name="status"> → 0 oder 1
):
    room = current_room(request)
    if room is None:
        return RedirectResponse(url="/rooms", status_code=302)

    conn, curs = get_db()

    # status umschalten, nur wenn gerät in diesem raum
    curs.execute("""
        UPDATE devices 
        SET status = ?
        WHERE device_id = ?
        AND room_id = ?
    """, (status, device_id, room["room_id"]))

    conn.commit()
    conn.close()

    return RedirectResponse(url="/devices/list", status_code=302)