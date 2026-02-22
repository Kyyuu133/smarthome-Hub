#Eigene Datei für die Class Device und später child class

class Device:
    def __init__(self, device_id, device_name, device_type, status, room_id, database, brightness=None):
        self.device_id = device_id
        self.device_name = device_name
        self.device_type = device_type
        self.status = bool(status)
        self.room_id = room_id
        self.database = database
        self.brightness = brightness # Ist standardmäßig auf NONE gesetzt wegen der anderen Geräte, die keine Brightness erlauvben

    def turn_on(self):
        self.status = True
        self._update_status_in_db()
        print(f"{self.device_name} turned ON")


    def turn_off(self):
        self.status = False
        self._update_status_in_db()
        print(f"{self.device_name} turned OFF")


    def set_brightness(self, level: int):
        # Setzt die Helligkeit (0–100). Nur für Geräte die Helligkeit unterstützen!
        if self.brightness is None:
            print(f"{self.device_name} does not support brightness control")
            return
        self.brightness = max(0, min(100, level))
        if self.brightness == 0:
            self.turn_off()
        else:
            self.turn_on() 

   
    def _update_status_in_db(self):

        conn = self.database.connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE devices
            SET status = ?
            WHERE device_id = ?
        """, (int(self.status), self.device_id))

        conn.commit()
        conn.close()
    
    def save_to_db(self):
        """Speichert das aktuelle Device in die DB"""
        conn = self.database.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO devices (device_name, device_type, status, room_id)
            VALUES (?, ?, ?, ?)
        """, (self.device_name, self.device_type, int(self.status), self.room_id))
        conn.commit()
        conn.close()
        print(f"{self.device_name} saved to DB")

   
    def print_info(self):
        state = "ON" if self.status else "OFF"
        brightness_str = f"\nBrightness: {self.brightness}%" if self.brightness is not None else ""

        print(f"""
        Device ID: {self.device_id}
        Name: {self.device_name}
        Type: {self.device_type}
        Room ID: {self.room_id}
        Status: {state}{brightness_str} 
        """) # Helligkeitsstatus hinzugefügt

class Lamp(Device):

    def __init__(self, device_id, device_name, status, room_id, database, brightness=0):
        
        
        super().__init__(
            device_id=device_id,
            device_name=device_name,
            device_type="Lamp",   
            status=status,
            room_id=room_id,
            database=database,
            brightness=brightness # Helligkeit nur hier hinzugefügt

        )


class alarm_clock(Device):

    def __init__(self, device_id, device_name, status, room_id, database, brightness=0):
        
        
        super().__init__(
            device_id=device_id,
            device_name=device_name,
            device_type="alarm_clock",   
            status=status,
            room_id=room_id,
            database=database
        )

class thermostat(Device):

    def __init__(self, device_id, device_name, status, room_id, database, brightness=0):
        
        
        super().__init__(
            device_id=device_id,
            device_name=device_name,
            device_type="thermostat",   
            status=status,
            room_id=room_id,
            database=database
        )
        # so erstellt man ein device und saved es

        #device1 = Device(
    #device_id=None,                            automatisch
    #device_name="Living Room Lamp",
    #device_type="Lamp",
    #status=0,                                  0 off 1 on
    #room_id=1,                     
    #database=db
#)

#  speichern
#lampe.save_to_db()
