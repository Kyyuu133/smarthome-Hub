import sqlite3
from device import Device
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from users_api import router as users_router
from rooms_devices_api import router as rooms_router
from database import Database
from fastapi.responses import RedirectResponse

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="SUPER_SECRET_KEY_123")  
# Mount both APIs under root

app.include_router(users_router)
app.include_router(rooms_router)

@app.get("/")
async def root():
    return RedirectResponse("/users/")

# class Database:
#     def __init__(self, db_path):
#         self.db_path = db_path

#     def connect(self):
#         conn = sqlite3.connect(self.db_path)
#         conn.row_factory = sqlite3.Row
#         return conn

# brauch die class nicht unbedingt aber empfohlen bei wachsenden projekten  
# Um die class zu nutzen muss man eine variable erstellen
#in unseren fall zb db = Database("useres_rooms_devices.sql")


class SmartHomeHub:

    def __init__(self, database):

        self.database = database
        self.devices = []

    # load all devices from database
    def load_devices(self):

        conn = self.database.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM devices")

        rows = cursor.fetchall()

        self.devices.clear()

        for row in rows:

            device = Device(
                device_id=row["device_id"],
                device_name=row["device_name"],
                device_type=row["device_type"],
                device_status=row["device_status"],
                room_id=row["room_id"],
                database=self.database
            )

            self.devices.append(device)

        conn.close()

    # get device object by id
    def get_device(self, device_id):

        for device in self.devices:

            if device.device_id == device_id:
                return device

        return None

    
    def delete_device(self, device_id):

        conn = self.database.connect()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM devices
            WHERE device_id = ?
        """, (device_id,))

        conn.commit()
        conn.close()

        
        self.devices = [
            device for device in self.devices
            if device.device_id != device_id
        ]

        print(f"Device {device_id} deleted")

    
    def list_devices(self):

        for device in self.devices:
            device.print_info()


# TEST / MAIN
if __name__ == "__main__":

    
    db = Database("useres_rooms_devices.sql")

    
    hub = SmartHomeHub(db)


    hub.load_devices()

    
    hub.list_devices()

   
    device = hub.get_device(1)

    if device:
        device.turn_on()

   
    hub.delete_device(2)

    hub.list_devices()
