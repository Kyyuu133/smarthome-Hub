from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from starlette.middleware.sessions import SessionMiddleware
import sqlite3
import os
from users_api import get_db, get_current_user
from rooms import Room
from database import Database
from rooms_devices_api import current_room

router = APIRouter(prefix="/rules", tags=["rules"])

templates = Jinja2Templates(directory="templates")

db_path = "hub.db"
db = Database(db_path)

@router.get("/", response_class=HTMLResponse)
async def check_rules(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse("/", status_code=303)

    # Direkt zur Regeln-Liste weiterleiten
    return RedirectResponse("/rules/list", status_code=303)


@router.get("/list", response_class=HTMLResponse)
async def get_rules(request: Request):
    """
    Listet alle Regeln auf (Admin-Ansicht oder eigene Regeln für User)
    """
    print("[DEBUG] Route /rules/list wurde aufgerufen")
    
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse("/", status_code=303)
    
    conn, curs = get_db()
    try:
        if current_user["user_role"] == "admin":
            # Admin sieht alle Regeln
            curs.execute("SELECT * FROM rules ORDER BY rules_id DESC")
        else:
            # User sieht nur Regeln für eigene/zugewiesene Räume
            curs.execute("""
                SELECT r.* FROM rules r
                WHERE r.room_id IN (
                    SELECT room_id FROM rooms WHERE user_id = ?
                    UNION
                    SELECT room_id FROM room_users WHERE user_id = ?
                )
                ORDER BY r.rules_id DESC
            """, (current_user["user_id"], current_user["user_id"]))
        
        rules = curs.fetchall()
        print(f"[DEBUG] {len(rules)} Regeln gefunden")
        
        return templates.TemplateResponse("rules/list.html", {
            "request": request,
            "rules": rules,
            "user": current_user
        })
    finally:
        conn.close()


@router.get("/room/{room_id}", response_class=HTMLResponse)
async def get_rules_room(request: Request, room_id: int):
    """
    Zeigt alle Regeln für einen spezifischen Raum
    """
    print(f"[DEBUG] Route /rules/room/{room_id} wurde aufgerufen")
    
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse("/", status_code=303)
    
    conn, curs = get_db()
    try:
        # Berechtigungsprüfung
        if current_user["user_role"] != "admin":
            curs.execute("""
                SELECT COUNT(*) FROM rooms 
                WHERE room_id = ? AND (
                    user_id = ? OR 
                    room_id IN (SELECT room_id FROM room_users WHERE user_id = ?)
                )
            """, (room_id, current_user["user_id"], current_user["user_id"]))
            
            if curs.fetchone()[0] == 0:
                return HTMLResponse("<h2>Keine Berechtigung für diesen Raum</h2>")
        
        # Raum-Infos holen
        curs.execute("SELECT * FROM rooms WHERE room_id = ?", (room_id,))
        room = curs.fetchone()
        
        if not room:
            return HTMLResponse("<h2>Raum nicht gefunden</h2>")
        
        # Regeln für diesen Raum holen
        curs.execute("SELECT * FROM rules WHERE room_id = ? ORDER BY rules_id DESC", (room_id,))
        rules = curs.fetchall()
        
        print(f"[DEBUG] {len(rules)} Regeln für Raum {room_id} gefunden")
        
        return templates.TemplateResponse("rules/room.html", {
            "request": request,
            "rules": rules,
            "room": room,
            "user": current_user
        })
    finally:
        conn.close()


@router.get("/device/{device_id}", response_class=HTMLResponse)
async def get_rules_device(request: Request, device_id: int):
    """
    Zeigt alle Regeln für ein spezifisches Gerät
    """
    print(f"[DEBUG] Route /rules/device/{device_id} wurde aufgerufen")
    
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse("/", status_code=303)
    
    conn, curs = get_db()
    try:
        # Device-Infos holen
        curs.execute("""
            SELECT d.*, r.room_name
            FROM devices d
            LEFT JOIN rooms r ON d.room_id = r.room_id
            WHERE d.device_id = ?
        """, (device_id,))
        device = curs.fetchone()
        
        if not device:
            return HTMLResponse("<h2>Gerät nicht gefunden</h2>")
        
        # Berechtigungsprüfung
        if current_user["user_role"] != "admin":
            curs.execute("""
                SELECT COUNT(*) FROM rooms 
                WHERE room_id = ? AND (
                    user_id = ? OR 
                    room_id IN (SELECT room_id FROM room_users WHERE user_id = ?)
                )
            """, (device["room_id"], current_user["user_id"], current_user["user_id"]))
            
            if curs.fetchone()[0] == 0:
                return HTMLResponse("<h2>Keine Berechtigung für dieses Gerät</h2>")
        
        # Regeln für dieses Gerät holen
        curs.execute("SELECT * FROM rules WHERE device_id = ? ORDER BY rules_id DESC", (device_id,))
        rules = curs.fetchall()
        
        print(f"[DEBUG] {len(rules)} Regeln für Device {device_id} gefunden")
        
        return templates.TemplateResponse("rules/device.html", {
            "request": request,
            "rules": rules,
            "device": device,
            "user": current_user
        })
    finally:
        conn.close()


@router.get("/create/{device_id}", response_class=HTMLResponse)
async def get_create_rule(request: Request, device_id: int):
    """
    Zeigt Formular zum Erstellen einer neuen Regel für ein Gerät
    """
    print(f"[DEBUG] Route /rules/create/{device_id} wurde aufgerufen")
    
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse("/", status_code=303)
    
    conn, curs = get_db()
    try:
        # Device-Infos holen
        curs.execute("""
            SELECT d.*, r.room_name
            FROM devices d
            LEFT JOIN rooms r ON d.room_id = r.room_id
            WHERE d.device_id = ?
        """, (device_id,))
        device = curs.fetchone()
        
        if not device:
            return HTMLResponse("<h2>Gerät nicht gefunden</h2>")
        
        # Berechtigungsprüfung
        if current_user["user_role"] != "admin":
            curs.execute("""
                SELECT COUNT(*) FROM rooms 
                WHERE room_id = ? AND (
                    user_id = ? OR 
                    room_id IN (SELECT room_id FROM room_users WHERE user_id = ?)
                )
            """, (device["room_id"], current_user["user_id"], current_user["user_id"]))
            
            if curs.fetchone()[0] == 0:
                return HTMLResponse("<h2>Keine Berechtigung für dieses Gerät</h2>")
        
        return templates.TemplateResponse("rules/create.html", {
            "request": request,
            "device": device,
            "user": current_user
        })
    finally:
        conn.close()


@router.post("/create/{device_id}", response_class=HTMLResponse)
async def post_create_rule(
    request: Request,
    device_id: int,
    temp_treshold_high: int = Form(0),
    temp_treshold_low: int = Form(0),
    brightness_treshold_high: int = Form(0),
    brightness_treshold_low: int = Form(0)
):
    """
    Erstellt eine neue Regel für ein Gerät
    """
    print(f"[DEBUG] POST /rules/create/{device_id}")
    
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse("/", status_code=303)

    conn, curs = get_db()
    try:
        # Device + Raum-Infos holen
        curs.execute("""
            SELECT d.device_id, d.device_name, d.device_type, d.device_status, 
                   d.room_id, r.room_name 
            FROM devices d
            JOIN rooms r ON d.room_id = r.room_id
            WHERE d.device_id = ?
        """, (device_id,))
        device = curs.fetchone()

        if not device:
            return HTMLResponse("<h2>Device existiert nicht</h2>")

        # Berechtigungsprüfung
        if current_user["user_role"] != "admin":
            curs.execute("""
                SELECT COUNT(*) FROM rooms 
                WHERE room_id = ? AND (
                    user_id = ? OR 
                    room_id IN (SELECT room_id FROM room_users WHERE user_id = ?)
                )
            """, (device["room_id"], current_user["user_id"], current_user["user_id"]))
            
            if curs.fetchone()[0] == 0:
                return HTMLResponse("<h2>Keine Berechtigung für dieses Gerät</h2>")

        # Regel einfügen (angepasst an dein Schema)
        curs.execute("""
            INSERT INTO rules (
                device_id, device_name, device_type, device_status,
                room_id, room_name,
                temp_treshold_high, temp_treshold_low,
                brightness_treshold_high, brightness_treshold_low
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            device["device_id"], device["device_name"], device["device_type"], device["device_status"],
            device["room_id"], device["room_name"],
            temp_treshold_high, temp_treshold_low,
            brightness_treshold_high, brightness_treshold_low
        ))
        conn.commit()
        
        print(f"[DEBUG] Regel erstellt für Device {device_id}")

    finally:
        conn.close()

    return RedirectResponse(f"/rules/device/{device_id}", status_code=303)


@router.get("/edit/{rules_id}", response_class=HTMLResponse)
async def get_edit_rule(request: Request, rules_id: int):
    """
    Zeigt Formular zum Bearbeiten einer Regel
    """
    print(f"[DEBUG] Route /rules/edit/{rules_id} wurde aufgerufen")
    
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse("/", status_code=303)

    conn, curs = get_db()
    try:
        # Regel holen
        curs.execute("SELECT * FROM rules WHERE rules_id = ?", (rules_id,))
        rule = curs.fetchone()

        if not rule:
            return HTMLResponse("<h2>Regel existiert nicht</h2>")

        # Berechtigungsprüfung
        if current_user["user_role"] != "admin":
            curs.execute("""
                SELECT COUNT(*) FROM rooms 
                WHERE room_id = ? AND (
                    user_id = ? OR 
                    room_id IN (SELECT room_id FROM room_users WHERE user_id = ?)
                )
            """, (rule["room_id"], current_user["user_id"], current_user["user_id"]))
            
            if curs.fetchone()[0] == 0:
                return HTMLResponse("<h2>Keine Berechtigung für diese Regel</h2>")

        return templates.TemplateResponse("rules/edit.html", {
            "request": request,
            "rule": rule,
            "user": current_user
        })
    finally:
        conn.close()


@router.post("/edit/{rules_id}", response_class=HTMLResponse)
async def post_edit_rule(
    request: Request,
    rules_id: int,
    temp_treshold_high: int = Form(0),
    temp_treshold_low: int = Form(0),
    brightness_treshold_high: int = Form(0),
    brightness_treshold_low: int = Form(0)
):
    """
    Aktualisiert eine bestehende Regel
    """
    print(f"[DEBUG] POST /rules/edit/{rules_id}")
    
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse("/", status_code=303)

    conn, curs = get_db()
    try:
        # Regel holen
        curs.execute("SELECT * FROM rules WHERE rules_id = ?", (rules_id,))
        rule = curs.fetchone()

        if not rule:
            return HTMLResponse("<h2>Regel existiert nicht</h2>")

        # Berechtigungsprüfung
        if current_user["user_role"] != "admin":
            curs.execute("""
                SELECT COUNT(*) FROM rooms 
                WHERE room_id = ? AND (
                    user_id = ? OR 
                    room_id IN (SELECT room_id FROM room_users WHERE user_id = ?)
                )
            """, (rule["room_id"], current_user["user_id"], current_user["user_id"]))
            
            if curs.fetchone()[0] == 0:
                return HTMLResponse("<h2>Keine Berechtigung für diese Regel</h2>")

        # Update
        curs.execute("""
            UPDATE rules SET
                temp_treshold_high = ?,
                temp_treshold_low = ?,
                brightness_treshold_high = ?,
                brightness_treshold_low = ?
            WHERE rules_id = ?
        """, (
            temp_treshold_high, temp_treshold_low,
            brightness_treshold_high, brightness_treshold_low,
            rules_id
        ))
        conn.commit()
        
        print(f"[DEBUG] Regel {rules_id} aktualisiert")

    finally:
        conn.close()

    return RedirectResponse(f"/rules/device/{rule['device_id']}", status_code=303)


@router.post("/delete/{rules_id}", response_class=HTMLResponse)
async def delete_rule(request: Request, rules_id: int):
    """
    Löscht eine Regel
    """
    print(f"[DEBUG] POST /rules/delete/{rules_id}")
    
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse("/", status_code=303)

    conn, curs = get_db()
    try:
        # Regel holen
        curs.execute("SELECT * FROM rules WHERE rules_id = ?", (rules_id,))
        rule = curs.fetchone()

        if not rule:
            return HTMLResponse("<h2>Regel existiert nicht</h2>")

        # Berechtigungsprüfung
        if current_user["user_role"] != "admin":
            curs.execute("""
                SELECT COUNT(*) FROM rooms 
                WHERE room_id = ? AND (
                    user_id = ? OR 
                    room_id IN (SELECT room_id FROM room_users WHERE user_id = ?)
                )
            """, (rule["room_id"], current_user["user_id"], current_user["user_id"]))
            
            if curs.fetchone()[0] == 0:
                return HTMLResponse("<h2>Keine Berechtigung für diese Regel</h2>")

        device_id = rule["device_id"]
        
        curs.execute("DELETE FROM rules WHERE rules_id = ?", (rules_id,))
        conn.commit()
        
        print(f"[DEBUG] Regel {rules_id} gelöscht")

    finally:
        conn.close()

    return RedirectResponse(f"/rules/device/{device_id}", status_code=303)