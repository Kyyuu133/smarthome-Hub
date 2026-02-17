from device import Device
from main import Database


db = Database("useres_rooms_devices.sql")

# Neues Device erstellen
device1 = Device(
    device_id=None,              
    device_name="Living Room Lamp",
    device_type="Lamp",
    status=0,                     
    room_id=1,                     
    database=db
)

# Device permanent in der DB speichern
device1.save_to_db()