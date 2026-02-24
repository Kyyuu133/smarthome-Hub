from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from starlette.middleware.sessions import SessionMiddleware
import sqlite3
import os
from users_api import get_db, get_current_user
from rooms import Room
from database import Database
from rooms_devices_api import current_room

router = APIRouter(prefix="/status", tags=["status"])

templates = Jinja2Templates(directory="templates")

db_path = "hub.db"
db = Database(db_path)


@router.get("/events", response_class=HTMLResponse)
async def get_status(request: Request):
    """
    Übersicht: prüft, ob Event-Einträge existieren.
    - Wenn keine Events vorhanden sind: Redirect zur Raumliste.
    - Sonst: rendert die Übersichtsvorlage.
    """
    print(f"[DEBUG] Route /status/events wurde aufgerufen")
    
    conn, curs = get_db()
    try:
        curs.execute("SELECT COUNT(*) FROM device_event_log")
        event_count = curs.fetchone()[0]
        print(f"[DEBUG] Event count: {event_count}")
    except sqlite3.OperationalError as e:
        print(f"[DEBUG] SQL Error: {e}")
        event_count = 0
    finally:
        conn.close()

    if event_count == 0:
        print("[DEBUG] Keine Events, Redirect zu /list")
        # Redirect zur Raumliste (keine Parameter nötig)
        return RedirectResponse("/list", status_code=303)
    
    print("[DEBUG] Rendering template: status/events/overview.html")
    return templates.TemplateResponse(
        "status/events/overview.html", 
        {"request": request}
    )


@router.get("/events/all_devices", response_class=HTMLResponse)
async def get_all_devices(request: Request):
    """
    Liefert jeweils das letzte Event für jede vorhandene device_id.
    """
    print(f"[DEBUG] Route /status/events/all_devices wurde aufgerufen")
    
    conn, curs = get_db()
    try:
        curs.execute("""
            SELECT *
            FROM device_event_log d
            WHERE event_id = (
                SELECT MAX(event_id) FROM device_event_log WHERE device_id = d.device_id
            )
            ORDER BY device_id
        """)
        events = curs.fetchall()
        print(f"[DEBUG] {len(events)} Events gefunden")
    except sqlite3.OperationalError as e:
        print(f"[DEBUG] SQL Error: {e}")
        events = []
    finally:
        conn.close()

    if not events:
        return RedirectResponse("/list", status_code=303)
    
    return templates.TemplateResponse(
        "status/all/devices.html", 
        {"request": request, "events": events}
    )


@router.get("/events/room", response_class=HTMLResponse)
async def get_room_events(request: Request):
    """
    Liefert Events für Geräte, die einem bestimmten Raum zugeordnet sind.
    """
    print(f"[DEBUG] Route /status/events/room wurde aufgerufen")
    
    conn, curs = get_db()
    room = current_room(request)
    
    if not room:
        print("[DEBUG] Kein Raum ausgewählt")
        return RedirectResponse("/list", status_code=303)
    
    print(f"[DEBUG] Raum ID: {room['room_id']}")
    
    try:
        curs.execute(
            "SELECT * FROM device_event_log "
            "WHERE device_id IN (SELECT device_id FROM devices WHERE room_id = ?) "
            "ORDER BY event_id DESC",
            (room["room_id"],)
        )
        events = curs.fetchall()
        print(f"[DEBUG] {len(events)} Events für Raum {room['room_id']} gefunden")
    except sqlite3.OperationalError as e:
        print(f"[DEBUG] SQL Error: {e}")
        events = []
    finally:
        conn.close()

    if not events:
        return RedirectResponse("/list", status_code=303)
    
    return templates.TemplateResponse(
        "status/events/room.html", 
        {"request": request, "events": events}
    )


@router.get("/events/history", response_class=HTMLResponse)
async def get_events_history(request: Request):
    """
    Allgemeine Ereignishistorie (neueste zuerst)
    """
    print(f"[DEBUG] Route /status/events/history wurde aufgerufen")
    
    conn, curs = get_db()
    try:
        curs.execute("SELECT * FROM device_event_log ORDER BY event_id DESC")
        events = curs.fetchall()
        print(f"[DEBUG] {len(events)} Events in der History gefunden")
    except sqlite3.OperationalError as e:
        print(f"[DEBUG] SQL Error: {e}")
        events = []
    finally:
        conn.close()

    if not events:
        return RedirectResponse("/list", status_code=303)
    
    return templates.TemplateResponse(
        "status/events/history.html", 
        {"request": request, "events": events}
    )


@router.get("/events/device/history/{device_id}", response_class=HTMLResponse)
async def get_device_history(request: Request, device_id: int):
    """
    Ereignishistorie für ein einzelnes Gerät (nach device_id)
    """
    print(f"[DEBUG] Route /status/events/device/history/{device_id} wurde aufgerufen")
    
    conn, curs = get_db()
    try:
        curs.execute(
            "SELECT * FROM device_event_log WHERE device_id = ? ORDER BY event_id DESC",
            (device_id,)
        )
        events = curs.fetchall()
        print(f"[DEBUG] {len(events)} Events für Device {device_id} gefunden")
    except sqlite3.OperationalError as e:
        print(f"[DEBUG] SQL Error: {e}")
        events = []
    finally:
        conn.close()

    if not events:
        return RedirectResponse("/list", status_code=303)
    
    return templates.TemplateResponse(
        "status/events/device_history.html", 
        {"request": request, "events": events, "device_id": device_id}
    )