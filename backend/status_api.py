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

# Zentrale SQL-Logik, um nur relevante Spalten zu laden
# Wenn Typ = Lamp -> Brightness laden, Temp = NULL
# Wenn Typ = Heater -> Temp laden, Brightness = NULL
SQL_FILTERED_SELECT = """
    SELECT 
        l.event_id, 
        l.device_id, 
        l.device_name, 
        l.device_status, 
        l.event_timestamp,
        d.device_type,
        CASE WHEN d.device_type = 'Lamp' THEN l.brightness_value ELSE NULL END as brightness_value,
        CASE WHEN d.device_type = 'Heater' THEN l.temp_value ELSE NULL END as temp_value
    FROM device_event_log l
    JOIN devices d ON l.device_id = d.device_id
"""

@router.get("/events", response_class=HTMLResponse)
async def get_status(request: Request):
    conn, curs = get_db()
    try:
        curs.execute("SELECT COUNT(*) FROM device_event_log")
        event_count = curs.fetchone()[0]
    except Exception:
        event_count = 0
    finally:
        conn.close()

    if event_count == 0:
        return RedirectResponse("/list", status_code=303)
    
    return templates.TemplateResponse("status/events/overview.html", {"request": request})

@router.get("/events/all_devices", response_class=HTMLResponse)
async def get_all_devices(request: Request):
    conn, curs = get_db()
    try:
        # Kombiniert den Filter mit der "Letztes Event pro Gerät" Logik
        query = f"""
            SELECT * FROM ({SQL_FILTERED_SELECT}) as filtered
            WHERE event_id = (
                SELECT MAX(event_id) FROM device_event_log WHERE device_id = filtered.device_id
            )
            ORDER BY device_id
        """
        curs.execute(query)
        events = [dict(row) for row in curs.fetchall()]
    except Exception as e:
        print(f"[DEBUG] Error: {e}")
        events = []
    finally:
        conn.close()

    if not events:
        return RedirectResponse("/list", status_code=303)
    return templates.TemplateResponse("status/all/devices.html", {"request": request, "events": events})

@router.get("/events/room", response_class=HTMLResponse)
async def get_room_events(request: Request):
    conn, curs = get_db()
    room = current_room(request)
    if not room:
        return RedirectResponse("/list", status_code=303)
    
    try:
        query = f"{SQL_FILTERED_SELECT} WHERE d.room_id = ? ORDER BY l.event_id DESC"
        curs.execute(query, (room["room_id"],))
        events = [dict(row) for row in curs.fetchall()]
    except Exception as e:
        print(f"[DEBUG] Error: {e}")
        events = []
    finally:
        conn.close()

    if not events:
        return RedirectResponse("/list", status_code=303)
    return templates.TemplateResponse("status/events/room.html", {"request": request, "events": events})

@router.get("/events/history", response_class=HTMLResponse)
async def get_events_history(request: Request):
    conn, curs = get_db()
    try:
        query = f"{SQL_FILTERED_SELECT} ORDER BY l.event_id DESC"
        curs.execute(query)
        events = [dict(row) for row in curs.fetchall()]
    except Exception as e:
        print(f"[DEBUG] Error: {e}")
        events = []
    finally:
        conn.close()

    if not events:
        return RedirectResponse("/list", status_code=303)
    return templates.TemplateResponse("status/events/history.html", {"request": request, "events": events})

@router.get("/events/device/history/{device_id}", response_class=HTMLResponse)
async def get_device_history(request: Request, device_id: int):
    conn, curs = get_db()
    try:
        query = f"{SQL_FILTERED_SELECT} WHERE l.device_id = ? ORDER BY l.event_id DESC"
        curs.execute(query, (device_id,))
        events = [dict(row) for row in curs.fetchall()]
    except Exception as e:
        print(f"[DEBUG] Error: {e}")
        events = []
    finally:
        conn.close()

    if not events:
        return RedirectResponse("/list", status_code=303)
    return templates.TemplateResponse(
        "status/events/device_history.html", 
        {"request": request, "events": events, "device_id": device_id}
    )