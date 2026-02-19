import sqlite3
from day_emulator import DayEmulator, default_device_callback
from device import Device


class Database:
    def __init__(self, db_path):
        self.db_path = db_path

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
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

    
    db = Database("hub.sql")

    
    hub = SmartHomeHub(db)


    hub.load_devices()

    # Emulator erstellen
    # speed = Sekunden pro simulierter Stunde (vorher einstellbar mit Float Nummern) 
    emulator = DayEmulator(database=db, speed=1.0, start_hour=0)

    # Automatischen Callback mit deinem Hub verknüpfen
    callback = default_device_callback(hub, temp_threshold_high=22.0, temp_threshold_low=16.0)

    # Tag simulieren – jede Stunde wird der Callback aufgerufen
    emulator.simulate_day(on_hour_callback=callback)

    # Nach der Simulation: Tagesprotokoll abrufen
    log = emulator.get_log()
    print(f"\nHours Protocol: {len(log)}")


    
    hub.list_devices()

   
    device = hub.get_device(1)

    if device:
        device.turn_on()

   
    hub.delete_device(2)

    hub.list_devices()
