import sqlite3
from device import Device, alarm_clock, Lamp, thermostat
from day_emulator_dimmable import DayEmulator, default_device_callback
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from users_api import router as users_router
from rooms_devices_api import router as rooms_router
from database import Database
from fastapi.responses import RedirectResponse

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="SUPER_SECRET_KEY_123")

app.include_router(users_router)
app.include_router(rooms_router)

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
                    database=self.database,
                    brightness=row["brightness"]
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

if __name__ == "__main__":
    db = Database("hub.db")
    hub = SmartHomeHub(db)
    hub.load_devices()

    emulator = DayEmulator(database=db, speed=1.0, start_hour=0)
    callback = default_device_callback(hub, temp_threshold_high=22.0, temp_threshold_low=16.0)
    emulator.simulate_day(on_hour_callback=callback)

    log = emulator.get_log()
    
    # Speichert Log von Helligkeit, Status und Temperatur direkt in den device_event_log
    conn = db.connect()
    cursor = conn.cursor()
    for entry in log:
        for device in hub.devices:
         cursor.execute("""
            INSERT INTO device_event_log 
                (device_id, device_status, event_timestamp, temp_value, brightness_value)
            VALUES (?, ?, ?, ?, ?)
        """, (
            device.device_id,
            int(device.device_status),
            f"2025-01-01 {entry['hour']:02d}:00:00",
            int(entry['temperature']),
            entry['brightness']
        ))
    conn.commit()
    conn.close()