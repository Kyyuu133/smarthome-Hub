from fastapi import APIRouter, Request, Form, Response              # FastAPI für Web-API
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
from database import Database                                         # Datenbank-Wrapper-Klasse

# HAUPTANWENDUNG SETUP

#app = FastAPI()                                                   # FastAPI-Anwendung erstellen
#app.add_middleware(SessionMiddleware, secret_key="SUPER_SECRET_KEY_123")  # Session-Middleware hinzufügen

router = APIRouter()

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
@router.get("/", response_class=HTMLResponse)
async def rooms_page(request: Request):
    """
    Startseite für Raumverwaltung:
    - Wenn KEINE Räume vorhanden: Zeige Formular zum Raum erstellen
    - Wenn Räume vorhanden: Leite zur Raum-Liste weiter
    """

    user = get_current_user(request)                    #logincheck
    if not user:
        return RedirectResponse("/", status_code=303)
    
    # Verbindung zur Datenbank öffnen
    conn, curs = get_db()

    if user["user_role"] == "admin":
        # Zähle, wie viele Räume in der Datenbank existieren falls admin
        curs.execute("SELECT COUNT(*) FROM rooms")
    else:
        # Zähle, wie viele Räume in der Datenbank existieren welche dem user zugeteilt sind
        curs.execute("SELECT COUNT(*) FROM rooms WHERE user_id = ?", (user["user_id"],))

    # Falls noch keine Daten in Tabelle → 0 Räume (rooms_count)
    rooms_count = curs.fetchone()[0]

    # Datenbankverbindung schließen
    conn.close()

    # KEINE Räume vorhanden → Formular zum Erstellen zeigen
    if rooms_count == 0:
        return templates.TemplateResponse("rooms/create.html", {"request": request})       
    # RÄUME vorhanden → Leite zur Raum-Liste weiter
    return RedirectResponse("/list", status_code=303)



# GET /rooms/list → Zeigt Liste aller verfügbaren Räume
@router.get("/list", response_class=HTMLResponse)
async def show_rooms_page(request: Request):
    """
    Zeigt alle Räume aus der Datenbank in einer HTML-Liste.
    """

    user = get_current_user(request)                #logincheck
    if not user:
        return RedirectResponse("/", status_code=303)
    
    # Verbindung zur Datenbank öffnen
    conn, curs = get_db()

    # Hole alle Räume aus der Datenbank
    if user["user_role"] == "admin":                #admin zugriff auf alle räume
        rooms = curs.execute("SELECT * FROM rooms").fetchall()
    else: 
        rooms = curs.execute(                       #user nur zugriff auf ihm zugewiesene räume
            "SELECT * FROM rooms WHERE user_id = ?",
            (user["user_id"],)
        ).fetchall()
    

    # Datenbankverbindung schließen
    conn.close()

    # Gebe die Raumliste im HTML-Template aus
    return templates.TemplateResponse("rooms/list.html", {
        "request": request,
        "rooms": rooms,
        "user": user
    })

# POST /rooms/create → Erstellt einen neuen Raum

@router.post("/create", response_class=HTMLResponse)
async def create_room(
    request: Request,
    room_name: str = Form(...)):

    """
    Erstellt einen neuen Raum:
    1. Prüft, ob Raumname bereits existiert
    2. Erstellt neuen Raum mit Benutzer-ID
    3. Leitet zur Raum-Liste weiter
    """

    user = get_current_user(request)                #logincheck
    if not user:
        return RedirectResponse("/", status_code=303)
        
    # Verbindung zur Datenbank öffnen
    conn, curs = get_db()

    # SICHERHEIT: Prüfe, ob dieser Raumname bereits existiert
    existing = curs.execute(
        "SELECT * FROM rooms WHERE room_name = ?", (room_name,)
    ).fetchone()

    if existing:        # FEHLERFALL: Raumname existiert bereits → Fehler anzeigen
        conn.close()
        return HTMLResponse("<h2>Room already exists.</h2>")
    
    curs.execute(
        "INSERT INTO rooms (room_name, user_id) VALUES (?,?)",(room_name, user["user_id"])
    )

    conn.commit()
    conn.close()

    # # Neues Room-Objekt erstellen
    # room = Room(
    #     room_id=None,                                   # ID wird automatisch generiert
    #     room_name=room_name,                            # Name aus Formular
    #     user_id=request.session.get("user_id"),         # Benutzer-ID aus Session
    #     database=db                                     # Datenbank-Verbindung
    # )
    # # Raum in Datenbank speichern
    # room.save_to_db()

    # ERFOLG: Leite zur Raum-Liste weiter
    return RedirectResponse(url="/list", status_code=303)

@router.get("/create", response_class=HTMLResponse)         #get damit wir vom browser zugreifen können
async def create_room_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("rooms/create.html", {"request": request})

# POST /rooms/delete → Löscht einen vorhandenen Raum

@router.post("/delete", response_class=HTMLResponse)
async def delete_room(
    request: Request,
    room_id: int = Form(...)
):
    """
    Löscht einen Raum und alle seine Geräte aus der Datenbank.
    """
    room = user_can_access_room(request, room_id)           #berechtigungs check und check ob raum existiert
    if not room:
        return HTMLResponse("<h2>Access not granted or room not existant.</h2>")

    conn, curs = get_db()

    curs.execute("DELETE FROM devices WHERE room_id = ?", (room_id,))   #lösche geräte aus raum
    curs.execute("DELETE FROM rooms WHERE room_id = ?", (room_id,))     #lösche raum aus rooms
    
    conn.commit()
    conn.close()

    # # SICHERHEIT: Prüfe, ob Raum-ID vorhanden ist
    # if not room_id:
    #     return templates.TemplateResponse("rooms/list.html", {
    #         "request": request,
    #         "error": "No Room-ID provided"
    #     })

    # # Neues Room-Objekt erstellen mit den Raum-Daten
    # room = Room(
    #     room_id=room_id,                                # Zu löschende Raum-ID
    #     room_name=room_name,                            # Name (für Info)
    #     user_id=request.session.get("user_id"),         # Benutzer-ID aus Session
    #     database=db                                     # Datenbank-Verbindung
    # )
    # # Raum aus Datenbank löschen
    # room.delete_from_db()

    # ERFOLG: Leite zurück zur Raum-Liste weiter
    return RedirectResponse(url="/list", status_code=303)

# PUT /rooms/rename → Benennt einen vorhandenen Raum um
@router.post("/rename")
async def rename_room(
    request: Request,
    room_id: int = Form(...),           
    new_name: str = Form(...)           
):
    """
    Ändert den Namen eines vorhandenen Raums.
    """
    room = user_can_access_room(request, room_id)
    
    if not room:
        return HTMLResponse("No Access.")
    conn, curs = get_db()

    curs.execute(
        "UPDATE rooms SET room_name = ? WHERE room_id = ?",
        (new_name, room_id)
    )

    conn.commit()
    conn.close()

    return RedirectResponse(url="/list", status_code=303)

    # # SICHERHEIT: Prüfe, ob Raum-ID und neuer Name vorhanden sind
    # if not room_id or not new_name:
    #     return templates.TemplateResponse("rooms/list.html", {
    #         "request": request,
    #         "error": "Keine Raum-ID oder neuer Name angegeben"
    #     })


#Devices

# ── GET /devices ── prüfen ob geräte vorhanden ────────────────────
@router.get("/devices", response_class=HTMLResponse)
async def devices_page(request: Request):
    room = current_room(request)
    if room is None:
        return RedirectResponse(url="/", status_code=302)

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



@router.get("/devices/list/room")
async def show_devices(request: Request, room_id: int):

    room = user_can_access_room(request, room_id)
    if not room:
        return RedirectResponse(url="/", status_code=303)

    conn, curs = get_db()

    devices = curs.execute(
        "SELECT * FROM devices WHERE room_id = ?",
        (room_id,)
        ).fetchall()

    conn.close()

    return templates.TemplateResponse("devices/list.html", {
        "request": request,
        "devices": devices,
        "room": room
    })

@router.get("/devices/list/all", response_class=HTMLResponse)
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

@router.post("/devices/create")
async def create_device(
    request: Request,
    room_id: int = Form(...),
    device_name: str = Form(...), 
    device_type: str = Form(...)
    ):

    room = user_can_access_room(request, room_id)
    if not room:
        return HTMLResponse("<h2>No Access.</h2>")

    conn, curs = get_db()

    # # prüfen ob gerät bereits existiert #nicht nötig, da nur existierende geräte ausgewählt werden können
    # existing = curs.execute(
    #     "SELECT * FROM devices WHERE device_name = ? AND device_id = ?", (device_name, device_id)
    # ).fetchone()

    # if existing:
    #     conn.close()
    #     return templates.TemplateResponse("devices/add.html", {
    #         "request": request,
    #         "room": room,
    #         "error": f"Gerät '{device_name}' existiert bereits"
    #     })

    # room_id kommt aus session, nicht aus dem formular
    curs.execute("""
        INSERT INTO devices (room_id, device_name, device_type, device_status)
        VALUES (?, ?, ?, 0)
    """, (room_id, device_name, device_type))

    conn.commit()
    conn.close()

    return RedirectResponse(f"/devices/list/room?room_id={room_id}", status_code=303)


# ── POST /devices/delete ── gerät löschen ─────────────────────────
@router.post("/devices/delete", response_class=HTMLResponse)
async def delete_device(
    request: Request,
    device_id: int = Form(...),
    room_id: int = Form(...)        # ← room_id aus dem Formular holen
):
    room = user_can_access_room(request, room_id)
    if not room:
        return HTMLResponse("<h2>No Access.</h2>")

    conn, curs = get_db()

    curs.execute("""
        DELETE FROM devices 
        WHERE device_id = ? 
        AND room_id = ?
    """, (device_id, room["room_id"]))

    conn.commit()
    conn.close()

    return RedirectResponse(f"/devices/list/room?room_id={room_id}", status_code=303)


# ── POST /devices/status ── gerät an/aus schalten ─────────────────
@router.post("/devices/status", response_class=HTMLResponse)
async def toggle_device_status(
    request: Request,
    device_id: int = Form(...),
    device_status: int = Form(...),
    room_id: int = Form(...)        # ← room_id aus Formular
):
    room = user_can_access_room(request, room_id)
    if not room:
        return HTMLResponse("<h2>No Access.</h2>")

    conn, curs = get_db()

    curs.execute("""
        UPDATE devices 
        SET device_status = ?
        WHERE device_id = ?
        AND room_id = ?
    """, (device_status, device_id, room_id))

    conn.commit()
    conn.close()

    return RedirectResponse(f"/devices/list/room?room_id={room_id}", status_code=303)

############################################# Kaan Additionen


def user_can_access_room(request: Request, room_id: int):       #neue funktion damit user je nach rolle auf räume zugreifen können
    user = get_current_user(request)
    if not user:                        #logincheck
        return False

    conn, curs = get_db()

    if user["user_role"] == "admin":
        room = curs.execute(
            "SELECT * FROM rooms WHERE room_id = ?",
            (room_id,)
        ).fetchone()
    else:
        room = curs.execute(
            "SELECT * FROM rooms WHERE room_id = ? AND user_id = ?",
            (room_id, user["user_id"])
        ).fetchone()

    conn.close()
    return room

@router.get("/devices/add", response_class=HTMLResponse)
async def add_device_page(request: Request, room_id: int):
    room = user_can_access_room(request, room_id)
    if not room:
        return RedirectResponse("/", status_code=303)

    return templates.TemplateResponse("devices/add.html", {
        "request": request,
        "room": room
    })