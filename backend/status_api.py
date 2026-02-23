from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from login import username_check, password_check
from typing import Optional
from starlette.middleware.sessions import SessionMiddleware
import sqlite3
import os
from users_api import get_db, get_current_user
from rooms import Room
from database import Database
from rooms_devices_api import current_room

router = APIRouter()

# Basisverzeichnis und Jinja2 Templates initialisieren
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Datenbank-Wrapper initialisieren (Pfad zur SQLite DB)
db_path = os.path.join(BASE_DIR, "hub.db")
db = Database(db_path)


@router.get("/status/events", response_class=HTMLResponse)
async def get_status(request: Request):
    """
    Übersicht: prüft, ob Event-Einträge existieren.
    - Wenn keine Events vorhanden sind: Redirect zur Geräte-Anlage.
    - Sonst: rendert die Übersichtsvorlage.
    """
    # Verbindung zur DB holen (get_db liefert conn, cursor)
    conn, curs = get_db()
    try:
        # Anzahl aller Einträge in device_event_log abfragen
        curs.execute("SELECT COUNT(*) FROM device_event_log")
        event_count = curs.fetchone()[0]
    except sqlite3.OperationalError:
        # Bei fehlender Tabelle o.ä. -> 0 Events annehmen
        event_count = 0
    finally:
        # Verbindung immer schließen, egal ob Fehler auftrat
        conn.close()

    if event_count == 0:
        # 303 See Other -> Weiterleitung zur Geräte-Add-Seite
        return RedirectResponse("/devices/add.html", status_code=303)
    # Template rendern, wenn Events existieren
    return templates.TemplateResponse("status/events/overview.html", {"request": request})


@router.get("/status/events/all_devices", response_class=HTMLResponse)
async def get_all_devices(request: Request):
    """
    Liefert jeweils das letzte Event für jede vorhandene device_id.
    - Query nutzt eine korrelierte Subquery, um das MAX(event_id) je device zu finden.
    - Ergebnis ist eine Liste mit einem Eintrag pro Gerät (letztes Event).
    """
    conn, curs = get_db()
    try:
        # Letztes Event pro device_id selektieren (korrelierte Subquery)
        curs.execute("""
            SELECT *
            FROM device_event_log d
            WHERE event_id = (
                SELECT MAX(event_id) FROM device_event_log WHERE device_id = d.device_id
            )
            ORDER BY device_id
        """)
        # Alle gefundenen Reihen abholen
        events = curs.fetchall()
    except sqlite3.OperationalError:
        # Falls Tabelle fehlt o.ä. -> leere Liste zurückgeben
        events = []
    finally:
        # DB-Verbindung schließen
        conn.close()

    if not events:
        # Wenn keine Events gefunden wurden -> Redirect zur Geräte-Anlage
        return RedirectResponse("/devices/add.html", status_code=303)
    # Template rendern mit den gefundenen Events
    return templates.TemplateResponse("status/all/devices.html", {"request": request, "events": events})


@router.get("/status/events/room", response_class=HTMLResponse)
async def get_room_events(request: Request):
    """
    Liefert Events für Geräte, die einem bestimmten Raum zugeordnet sind.
    - current_room() liefert die aktive Raum-ID.
    - Hier werden alle Events der Geräte im Raum zurückgegeben, absteigend nach event_id.
    """
    # Verbindung und Cursor holen
    conn, curs = get_db()
    # Raum-ID aus rooms_devices_api (falls None, Query liefert keine Geräte)
    room = current_room()
    try:
        # Alle Events für Geräte in diesem Raum, sortiert nach neustem Event zuerst
        curs.execute(
            "SELECT * FROM device_event_log "
            "WHERE device_id IN (SELECT device_id FROM rooms WHERE room_id = ?) "
            "ORDER BY event_id DESC",
            (room,)
        )
        # Ergebnisse holen
        events = curs.fetchall()
    except sqlite3.OperationalError:
        # Bei Fehlern (z. B. fehlende Tabellen) -> leere Liste
        events = []
    finally:
        # Verbindung immer schließen
        conn.close()

    if not events:
        # Keine Events -> Redirect zur Geräte-Anlage
        return RedirectResponse("/devices/add.html", status_code=303)
    # Template mit den Raum-Events rendern
    return templates.TemplateResponse("status/events/room.html", {"request": request, "events": events})


@router.get("/status/events/history", response_class=HTMLResponse)
async def get_events_history(request: Request):
    # Allgemeine Ereignishistorie (neueste zuerst)
    conn, curs = get_db()
    try:
        curs.execute("SELECT * FROM device_event_log ORDER BY event_id DESC")
        events = curs.fetchall()
    except sqlite3.OperationalError:
        # Falls Tabelle fehlt oder andere DB-Fehler -> leere Liste
        events = []
    finally:
        conn.close()

    if not events:
        # Wenn keine Events vorhanden -> Redirect zur Geräte-Anlage
        return RedirectResponse("/devices/add.html", status_code=303)
    # Template mit allen Events rendern
    return templates.TemplateResponse("status/events/history.html", {"request": request, "events": events})


@router.get("/status/events/device/history/{device_id}", response_class=HTMLResponse)
async def get_device_history(request: Request, device_id: int):
    # Ereignishistorie für ein einzelnes Gerät (nach device_id)
    conn, curs = get_db()
    try:
        curs.execute(
            "SELECT * FROM device_event_log WHERE device_id = ? ORDER BY event_id DESC",
            (device_id,)
        )
        events = curs.fetchall()
    except sqlite3.OperationalError:
        # Bei Fehlern -> leere Ergebnisliste
        events = []
    finally:
        # Verbindung schließen
        conn.close()

    if not events:
        # Keine Events für dieses Gerät -> Redirect
        return RedirectResponse("/devices/add.html", status_code=303)
    # Template für Geräteeinträge rendern, device_id zur Anzeige mitgeben
    return templates.TemplateResponse("status/events/device_history.html", {"request": request, "events": events, "device_id": device_id})