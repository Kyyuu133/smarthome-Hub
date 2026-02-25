class Device:
    def __init__(self, device_id, device_name, device_type, device_status, room_id, database):
        self.device_id = device_id
        self.device_name = device_name
        self.device_type = device_type
        self.device_status = bool(device_status)
        self.room_id = room_id
        self.database = database
        self.brightness = None
        

    def turn_on(self):
        self.device_status = True
        self._update_status_in_db()
        print(f"{self.device_name} turned ON")

    def turn_off(self):
        self.device_status = False
        self._update_status_in_db()
        print(f"{self.device_name} turned OFF")

    

    def _update_status_in_db(self):
        conn = self.database.connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE devices
            SET device_status = ?
            WHERE device_id = ?
        """, (int(self.device_status), self.device_id))

        conn.commit()
        conn.close()

    def save_to_db(self):
        """Speichert das aktuelle Device in die DB"""
        conn = self.database.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO devices (device_name, device_type, device_status, room_id)
            VALUES (?, ?, ?, ?)
        """, (self.device_name, self.device_type, int(self.device_status), self.room_id))
        cursor.execute("""
            INSERT INTO device_event_log (event_log, device_id, device_status)
            VALUES (, ?, ?)
        """, 
            (self.device_id, int(self.device_status))
        )

        conn.commit()
        conn.close()
        print(f"{self.device_name} saved to DB")

    def print_info(self):
        state = "ON" if self.device_status else "OFF"
        brightness_str = f"\nBrightness: {self.brightness}%" if self.brightness is not None else ""

        print(f"""
        Device ID: {self.device_id}
        Name: {self.device_name}
        Type: {self.device_type}
        Room ID: {self.room_id}
        Status: {state}{brightness_str}
        """)


class Lamp(Device):
    def __init__(self, device_id, device_name, device_status, room_id, database, brightness=0):
        super().__init__(
            device_id=device_id,
            device_name=device_name,
            device_type="Lamp",
            device_status=device_status,
            room_id=room_id,
            database=database
            )
        self.brightness = brightness

    def set_brightness(self, level: int):
        """Setzt die Helligkeit (0–100). Nur für Geräte mit Brightness."""
        if self.brightness == 0:
            print(f"{self.device_name} does not support brightness control")
            return

        self.brightness = max(0, min(100, level))

        if self.brightness == 0:
            self.turn_off()
        else:
            self.turn_on()


class alarm_clock(Device):
    def __init__(self, device_id, device_name, device_status, room_id, database):
        super().__init__(
            device_id=device_id,
            device_name=device_name,
            device_type="alarm_clock",
            device_status=device_status,
            room_id=room_id,
            database=database
        )




class Heater(Device):
    def __init__(self, device_id, device_name, device_status, room_id, database):
        super().__init__(
            device_id=device_id,
            device_name=device_name,
            device_type="Heater",
            device_status=device_status,
            room_id=room_id,
            database=database
        )
        
    def check_temperature(self, current_temperature: float):
        """
        Schaltet den Heater automatisch:
        - EIN bei <= 8°C
        - AUS bei >= 20°C
        """
        if current_temperature <= 8:
            if not self.device_status:
                print(f"{self.device_name}: {current_temperature}°C → Heater ON")
                self.turn_on()

        elif current_temperature >= 20:
            if self.device_status:
                print(f"{self.device_name}: {current_temperature}°C → Heater OFF")
                self.turn_off()