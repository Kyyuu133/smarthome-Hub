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

router = APIRouter(prefix="/status", tags=["status"])

templates = Jinja2Templates(directory="templates")

db_path = "hub.db"
db = Database(db_path)

@router.get("/rules/", response_class=HTMLResponse)
async def check_rules(request: Request):
    """
    Übersicht: prüft, ob Regeln existieren.
    """
    conn, curs = get_db()
    try:
        curs.execute("SELECT COUNT(*) FROM rule")
        rule_count = curs.fetchone()[0]
        if rule_count == 0:
            # Redirect zur Raumliste (keine Parameter nötig)
            return RedirectResponse("/list", status_code=303)
        else:
            # Redirect zur Regelübersicht (keine Parameter nötig)
            return RedirectResponse("/rules/list")
    finally:
      conn.close()

#get all rules - für admin übersicht maybe dachte ich    
@router.get("/rules/list", response_class=HTMLResponse)
async def get_rules(request: Request):
    """
    Listet alle Regeln auf für die Admin-Ansicht
    """
    conn, curs = get_db()
    try:
        curs.execute("SELECT * FROM rule")
        rules = curs.fetchall()
        return templates.TemplateResponse("rules/list.html", 
            {"request": request, "rules": rules})
    finally:
        conn.close()
        
#get rules for room
@router.get("/rules/room/{room_id}", response_class=HTMLResponse)
async def get_rules_room(request: Request, room_id):
    """
    Zeigt alle Rules für einen spezifischen Raum(room_id)
    """
    conn, curs = get_db()
    try:
        curs.execute("SELECT * FROM rule WHERE room_id = ?", (room_id,))
        rules = curs.fetchall()
        return templates.TemplateResponse("rules/room.html", 
            {"request": request, "rules": rules})
    finally:
        conn.close()
        
#get rules device
@router.get("/rules/device/{devic_id}", response_class=HTMLResponse)
async def get_rules_device(request: Request, devic_id):
    """
    Zeigt alle Rules für einen spezifischen Gerät(devic_id)
    """
    conn, curs = get_db()
    try:
        curs.execute("SELECT * FROM rule WHERE devic_id = ?", (devic_id,))
        rules = curs.fetchall()
        return templates.TemplateResponse("rules/device.html", 
            {"request": request, "rules": rules})
    finally:
        conn.close()
        
@router.post("/rules/device/{device_id}", response_class=HTMLResponse)
async def post_rule(
    request: Request,
    device_id: int,
    temp_treshold_high: int = Form(...),
    temp_treshold_low: int = Form(...),
    brightness_treshold_high: int = Form(...),
    brightness_treshold_low: int = Form(...)
):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    conn, curs = get_db()
    try:
        # Device + zugehörige Raum-Infos holen
        curs.execute("""
            SELECT d.device_id, d.device_name, d.device_type, d.device_status, 
                   d.room_id, r.room_name 
            FROM devices d
            JOIN rooms r ON d.room_id = r.room_id
            WHERE d.device_id = ?
        """, (device_id,))
        device = curs.fetchone()

        if not device:
            return templates.TemplateResponse("error.html", {
                "request": request, "message": "Device existiert nicht"
            })

        dev_id, dev_name, dev_type, dev_status, room_id, room_name = device

        # Berechtigungsprüfung: Admin darf alles, User nur eigene Räume
        if current_user["user_role"] != "admin":
            curs.execute("""
                SELECT COUNT(*) FROM room_users 
                WHERE room_id = ? AND user_id = ?
            """, (room_id, current_user["user_id"]))
            if curs.fetchone()[0] == 0:
                return templates.TemplateResponse("error.html", {
                    "request": request, "message": "Keine Berechtigung für dieses Gerät"
                })

        # Regel einfügen
        curs.execute("""
            INSERT INTO rules (
                device_id, device_name, device_type, device_status,
                room_id, room_name,
                temp_treshold_high, temp_treshold_low,
                brightness_treshold_high, brightness_treshold_low
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dev_id, dev_name, dev_type, dev_status,
            room_id, room_name,
            temp_treshold_high, temp_treshold_low,
            brightness_treshold_high, brightness_treshold_low
        ))
        conn.commit()

    finally:
        conn.close()

    return RedirectResponse(f"/status/rules/device/{device_id}", status_code=303)


# get edit a specific rule
@router.get("/rules/edit/{rules_id}", response_class=HTMLResponse)
async def get_edit_rule(request: Request, rules_id: int):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    conn, curs = get_db()
    try:
        # Regel holen
        curs.execute("SELECT * FROM rules WHERE rules_id = ?", (rules_id,))
        rule = curs.fetchone()

        if not rule:
            return templates.TemplateResponse("error.html", {
                "request": request, "message": "Regel existiert nicht"
            })

        # Berechtigungsprüfung
        if current_user["user_role"] != "admin":
            curs.execute("""
                SELECT COUNT(*) FROM room_users 
                WHERE room_id = ? AND user_id = ?
            """, (rule["room_id"], current_user["user_id"]))
            if curs.fetchone()[0] == 0:
                return templates.TemplateResponse("error.html", {
                    "request": request, "message": "Keine Berechtigung für diese Regel"
                })

        return templates.TemplateResponse("rules/edit.html", {
            "request": request, "rule": rule
        })
    finally:
        conn.close()


# post edit rules for a specific rule
@router.post("/rules/edit/{rules_id}", response_class=HTMLResponse)
async def post_edit_rule(
    request: Request,
    rules_id: int,
    temp_treshold_high: int = Form(...),
    temp_treshold_low: int = Form(...),
    brightness_treshold_high: int = Form(...),
    brightness_treshold_low: int = Form(...)
):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    conn, curs = get_db()
    try:
        # Regel holen um room_id für Berechtigungsprüfung zu bekommen
        curs.execute("SELECT room_id FROM rules WHERE rules_id = ?", (rules_id,))
        rule = curs.fetchone()

        if not rule:
            return templates.TemplateResponse("error.html", {
                "request": request, "message": "Regel existiert nicht"
            })

        # Berechtigungsprüfung
        if current_user["user_role"] != "admin":
            curs.execute("""
                SELECT COUNT(*) FROM room_users 
                WHERE room_id = ? AND user_id = ?
            """, (rule["room_id"], current_user["user_id"]))
            if curs.fetchone()[0] == 0:
                return templates.TemplateResponse("error.html", {
                    "request": request, "message": "Keine Berechtigung für diese Regel"
                })

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

    finally:
        conn.close()

    return RedirectResponse(f"/status/rules/device/{rule['device_id']}", status_code=303)

#delete rule device

@router.post("/rules/delete/{rules_id}", response_class=HTMLResponse)
async def delete_rule(request: Request, rules_id: int):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    conn, curs = get_db()
    try:
        # Regel holen für Berechtigungsprüfung
        curs.execute("SELECT * FROM rules WHERE rules_id = ?", (rules_id,))
        rule = curs.fetchone()

        if not rule:
            return templates.TemplateResponse("error.html", {
                "request": request, "message": "Regel existiert nicht"
            })

        # Berechtigungsprüfung
        if current_user["user_role"] != "admin":
            curs.execute("""
                SELECT COUNT(*) FROM room_users 
                WHERE room_id = ? AND user_id = ?
            """, (rule["room_id"], current_user["user_id"]))
            if curs.fetchone()[0] == 0:
                return templates.TemplateResponse("error.html", {
                    "request": request, "message": "Keine Berechtigung für diese Regel"
                })

        curs.execute("DELETE FROM rules WHERE rules_id = ?", (rules_id,))
        conn.commit()

    finally:
        conn.close()

    return RedirectResponse(f"/status/rules/device/{rule['device_id']}", status_code=303)


