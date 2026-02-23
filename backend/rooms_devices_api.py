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

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

db_path = os.path.join(BASE_DIR, "hub.db")
db = Database(db_path)


def current_room(request: Request):
    room_id = request.session.get("room_id")
    user_id = request.session.get("user_id")
    user_role = request.session.get("user_role")

    if room_id is None:
        return None

    conn, curs = get_db()

    if user_role == "admin":
        room = curs.execute("""
            SELECT room_id, room_name, user_id 
            FROM rooms 
            WHERE room_id = ?
        """, (room_id,)).fetchone()
    else:
        room = curs.execute("""
            SELECT room_id, room_name, user_id 
            FROM rooms 
            WHERE room_id = ? 
            AND user_id = ?;
        """, (room_id, user_id)).fetchone()

    conn.close()

    if room is None:
        request.session.pop("room_id", None)
        return None

    return room


@router.get("/", response_class=HTMLResponse)
async def rooms_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/", status_code=303)

    conn, curs = get_db()

    if user["user_role"] == "admin":
        curs.execute("SELECT COUNT(*) FROM rooms")
    else:
        # Zähle eigene + zugewiesene Räume
        curs.execute("""
            SELECT COUNT(*) FROM (
                SELECT room_id FROM rooms WHERE user_id = ?
                UNION
                SELECT room_id FROM room_users WHERE user_id = ?
            )
        """, (user["user_id"], user["user_id"]))

    rooms_count = curs.fetchone()[0]
    conn.close()

    if rooms_count == 0:
        return templates.TemplateResponse("rooms/create.html", {"request": request})
    return RedirectResponse("/list", status_code=303)


@router.get("/list", response_class=HTMLResponse)
async def show_rooms_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/", status_code=303)

    conn, curs = get_db()

    if user["user_role"] == "admin":
        rooms = curs.execute("SELECT * FROM rooms").fetchall()
    else:
        rooms = curs.execute("""
            SELECT * FROM rooms 
            WHERE user_id = ?
            UNION
            SELECT r.* FROM rooms r
            JOIN room_users ru ON r.room_id = ru.room_id
            WHERE ru.user_id = ?
        """, (user["user_id"], user["user_id"])).fetchall()

    all_users = []
    rooms_with_users = []

    if user["user_role"] == "admin":
        all_users = curs.execute("SELECT * FROM users").fetchall()

        for room in rooms:
            assigned = curs.execute("""
                SELECT u.user_id, u.user_name
                FROM room_users ru
                JOIN users u ON ru.user_id = u.user_id
                WHERE ru.room_id = ?
            """, (room["room_id"],)).fetchall()
            room_dict = dict(room)
            room_dict["assigned_users"] = [dict(a) for a in assigned]
            rooms_with_users.append(room_dict)
    else:
        rooms_with_users = [dict(r) | {"assigned_users": []} for r in rooms]

    conn.close()

    return templates.TemplateResponse("rooms/list.html", {
        "request": request,
        "rooms": rooms_with_users,
        "user": user,
        "all_users": all_users
    })


@router.post("/create", response_class=HTMLResponse)
async def create_room(request: Request, room_name: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/", status_code=303)

    conn, curs = get_db()

    existing = curs.execute(
        "SELECT * FROM rooms WHERE room_name = ?", (room_name,)
    ).fetchone()

    if existing:
        conn.close()
        return HTMLResponse("<h2>Room already exists.</h2>")

    curs.execute(
        "INSERT INTO rooms (room_name, user_id) VALUES (?,?)", (room_name, user["user_id"])
    )

    conn.commit()
    conn.close()

    return RedirectResponse(url="/list", status_code=303)


@router.get("/create", response_class=HTMLResponse)
async def create_room_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("rooms/create.html", {"request": request})


@router.post("/delete", response_class=HTMLResponse)
async def delete_room(request: Request, room_id: int = Form(...)):
    room = user_can_access_room(request, room_id)
    if not room:
        return HTMLResponse("<h2>Access not granted or room not existant.</h2>")

    conn, curs = get_db()
    curs.execute("DELETE FROM devices WHERE room_id = ?", (room_id,))
    curs.execute("DELETE FROM rooms WHERE room_id = ?", (room_id,))
    conn.commit()
    conn.close()

    return RedirectResponse(url="/list", status_code=303)


@router.post("/rename")
async def rename_room(request: Request, room_id: int = Form(...), new_name: str = Form(...)):
    room = user_can_access_room(request, room_id)
    if not room:
        return HTMLResponse("No Access.")

    conn, curs = get_db()
    curs.execute("UPDATE rooms SET room_name = ? WHERE room_id = ?", (new_name, room_id))
    conn.commit()
    conn.close()

    return RedirectResponse(url="/list", status_code=303)


# ── GET /devices ──────────────────────────────────────────────────
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

    if devices_count == 0:
        return templates.TemplateResponse("devices/add.html", {"request": request, "room": room})

    return RedirectResponse(url="/devices/list", status_code=302)


@router.get("/devices/list/room")
async def show_devices(request: Request, room_id: int):
    room = user_can_access_room(request, room_id)
    if not room:
        return RedirectResponse(url="/", status_code=303)

    conn, curs = get_db()
    devices = curs.execute("SELECT * FROM devices WHERE room_id = ?", (room_id,)).fetchall()
    conn.close()

    return templates.TemplateResponse("devices/list.html", {
        "request": request,
        "devices": devices,
        "room": room
    })


@router.get("/devices/list/all", response_class=HTMLResponse)
async def show_all_devices(request: Request):
    conn, curs = get_db()
    devices = curs.execute("SELECT * FROM devices").fetchall()
    conn.close()
    return templates.TemplateResponse("devices/list_all.html", {"request": request, "devices": devices})


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
    curs.execute("""
        INSERT INTO devices (room_id, device_name, device_type, device_status)
        VALUES (?, ?, ?, 0)
    """, (room_id, device_name, device_type))
    conn.commit()
    conn.close()

    return RedirectResponse(f"/devices/list/room?room_id={room_id}", status_code=303)


@router.post("/devices/delete", response_class=HTMLResponse)
async def delete_device(request: Request, device_id: int = Form(...), room_id: int = Form(...)):
    room = user_can_access_room(request, room_id)
    if not room:
        return HTMLResponse("<h2>No Access.</h2>")

    conn, curs = get_db()
    curs.execute("DELETE FROM devices WHERE device_id = ? AND room_id = ?", (device_id, room["room_id"]))
    conn.commit()
    conn.close()

    return RedirectResponse(f"/devices/list/room?room_id={room_id}", status_code=303)


@router.post("/devices/status", response_class=HTMLResponse)
async def toggle_device_status(
    request: Request,
    device_id: int = Form(...),
    device_status: int = Form(...),
    room_id: int = Form(...)
):
    room = user_can_access_room(request, room_id)
    if not room:
        return HTMLResponse("<h2>No Access.</h2>")

    conn, curs = get_db()
    curs.execute("""
        UPDATE devices SET device_status = ?
        WHERE device_id = ? AND room_id = ?
    """, (device_status, device_id, room_id))
    conn.commit()
    conn.close()

    return RedirectResponse(f"/devices/list/room?room_id={room_id}", status_code=303)


def user_can_access_room(request: Request, room_id: int):
    user = get_current_user(request)
    if not user:
        return False

    conn, curs = get_db()

    if user["user_role"] == "admin":
        room = curs.execute(
            "SELECT * FROM rooms WHERE room_id = ?", (room_id,)
        ).fetchone()
    else:
        # user hat zugriff wenn er der ersteller ist ODER ihm der raum zugewiesen wurde
        room = curs.execute("""
            SELECT * FROM rooms WHERE room_id = ? AND (
                user_id = ?
                OR room_id IN (SELECT room_id FROM room_users WHERE user_id = ?)
            )""",
            (room_id, user["user_id"], user["user_id"])
        ).fetchone()

    conn.close()
    return room


@router.get("/devices/add", response_class=HTMLResponse)
async def add_device_page(request: Request, room_id: int):
    room = user_can_access_room(request, room_id)
    if not room:
        return RedirectResponse("/", status_code=303)

    return templates.TemplateResponse("devices/add.html", {"request": request, "room": room})


# ── POST /assign_user ── admin weist user einem raum zu ──────────
@router.post("/assign_user", response_class=HTMLResponse)
async def assign_user_to_room(request: Request, room_id: int = Form(...), user_id: int = Form(...)):
    current_user = get_current_user(request)
    if not current_user or current_user["user_role"] != "admin":
        return HTMLResponse("<h2>Keine Berechtigung.</h2>")

    conn, curs = get_db()

    room = curs.execute("SELECT * FROM rooms WHERE room_id = ?", (room_id,)).fetchone()
    if not room:
        conn.close()
        return HTMLResponse("<h2>Raum nicht gefunden.</h2>")

    curs.execute(
        "INSERT OR IGNORE INTO room_users (room_id, user_id) VALUES (?, ?)",
        (room_id, user_id)
    )
    conn.commit()
    conn.close()

    return RedirectResponse("/list", status_code=303)


# ── POST /unassign_user ── admin entfernt user aus raum ──────────
@router.post("/unassign_user", response_class=HTMLResponse)
async def unassign_user_from_room(request: Request, room_id: int = Form(...), user_id: int = Form(...)):
    current_user = get_current_user(request)
    if not current_user or current_user["user_role"] != "admin":
        return HTMLResponse("<h2>Keine Berechtigung.</h2>")

    conn, curs = get_db()
    curs.execute("DELETE FROM room_users WHERE room_id = ? AND user_id = ?", (room_id, user_id))
    conn.commit()
    conn.close()

    return RedirectResponse("/list", status_code=303)