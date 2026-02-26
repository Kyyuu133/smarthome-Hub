import sqlite3
from device import Device, alarm_clock, Lamp
from emulator import DayEmulator, default_device_callback
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from users_api import router as users_router
from rooms_devices_api import router as rooms_router
from database import Database
from fastapi.responses import RedirectResponse
from status_api import router as status_router
from datetime import datetime
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="SUPER_SECRET_KEY_123")

app.include_router(users_router)
app.include_router(rooms_router)
app.include_router(status_router)

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root():
    return RedirectResponse("/users/")

class SmartHomeHub:
    def __init__(self, database):
        self.database = database
        self.devices = []

    def load_devices(self):
        conn = self.database.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM devices")
        rows = cursor.fetchall()
        self.devices.clear()
       
       
        for row in rows:
            device_type = row["device_type"]
            if device_type == "Lamp":
                device = Lamp(
                    device_id=row["device_id"],
                    device_name=row["device_name"],
                    device_status=row["device_status"],
                    room_id=row["room_id"],
                    database=self.database#,
                    #brightness=row["brightness"]
                )
            elif device_type == "alarm_clock":
                device = alarm_clock(
                    device_id=row["device_id"],
                    device_name=row["device_name"],
                    device_status=row["device_status"],
                    room_id=row["room_id"],
                    database=self.database
                )
            else:
                device = Device(
                    device_id=row["device_id"],
                    device_name=row["device_name"],
                    device_type=row["device_type"],
                    device_status=row["device_status"],   # ← DB Spalte heißt device_status
                    room_id=row["room_id"],
                    database=self.database
                )
            self.devices.append(device)
        conn.close()

    def get_device(self, device_id):
        for device in self.devices:
            if device.device_id == device_id:
                return device
        return None

    def delete_device(self, device_id):
        conn = self.database.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM devices WHERE device_id = ?", (device_id,))
        conn.commit()
        conn.close()
        self.devices = [d for d in self.devices if d.device_id != device_id]
        print(f"Device {device_id} deleted")

    def list_devices(self):
        for device in self.devices:
            device.print_info()

def run_simulation():
    db = Database("hub.db")
    hub = SmartHomeHub(db)
    hub.load_devices()

    emulator = DayEmulator(database=db, speed=1.0, start_hour=0)
    
    # NEU: Dictionary zum Speichern der Stati pro Stunde
    hourly_device_states = {}
    
    # NEU: Callback der zusätzlich einen Snapshot der Stati speichert
    base_callback = default_device_callback(hub)
    def callback_with_snapshot(hour, temp, tod, brightness=0):
        base_callback(hour, temp, tod, brightness=brightness)
        hourly_device_states[hour] = {
            d.device_id: int(d.device_status) for d in hub.devices
        }

    # GEÄNDERT: callback_with_snapshot statt callback übergeben
    emulator.simulate_day(on_hour_callback=callback_with_snapshot)

    log = emulator.get_log()
    today = datetime.now().strftime("%Y-%m-%d")

    conn = db.connect()
    cursor = conn.cursor()

    for entry in log:
        for device in hub.devices:

            temp_value = None
            brightness_value = None

            if device.device_type == "Heater":
                temp_value = entry["temperature"]

            if device.device_type == "Lamp":
                brightness_value = entry["brightness"]

            # GEÄNDERT: Status aus hourly_device_states holen statt device.device_status
            status_at_hour = hourly_device_states.get(entry["hour"], {}).get(device.device_id, 0)

            cursor.execute("""
                INSERT INTO device_event_log 
                (device_id, device_name, device_type,
                 device_status, event_timestamp,
                 temp_value, brightness_value)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                device.device_id,
                device.device_name,
                device.device_type,
                status_at_hour,   # ← GEÄNDERT
                f"{today} {entry['hour']:02d}:00:00",
                temp_value,
                brightness_value
            ))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    run_simulation()