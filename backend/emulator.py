"""
Day Emulator für das Smart Home System
Simuliert einen 24-Stunden-Tag mit Temperaturveränderungen.
"""

import time
import random
import sqlite3
from datetime import datetime


# Temperaturprofil für einen typischen Tag (Stunde -> Basistemperatur in °C)
TEMP_PROFILE = {
    0:  16.0,
    1:  15.5,
    2:  15.0,
    3:  14.5,
    4:  14.0,
    5:  14.0,
    6:  14.5,
    7:  15.5,
    8:  17.0,
    9:  18.5,
    10: 20.0,
    11: 21.5,
    12: 23.0,
    13: 24.0,
    14: 24.5,
    15: 24.0,
    16: 23.0,
    17: 21.5,
    18: 20.0,
    19: 19.0,
    20: 18.0,
    21: 17.5,
    22: 17.0,
    23: 16.5,
}

# Brightness profile for lamps (hour -> brightness in %, 0 = off, 100 = full)
# Lamps are bright at night, dim during transitions, off during daytime
BRIGHTNESS_PROFILE = {
    0:  100,
    1:  100,
    2:  100,
    3:  100,
    4:  100,
    5:  80,
    6:  60,
    7:  30,
    8:  0,
    9:  0,
    10: 0,
    11: 0,
    12: 0,
    13: 0,
    14: 0,
    15: 0,
    16: 0,
    17: 0,
    18: 20,
    19: 50,
    20: 80,
    21: 100,
    22: 100,
    23: 100,
}


def get_temperature_at_hour(hour: int) -> float:
    """
    Gibt die simulierte Temperatur für eine bestimmte Stunde zurück.
    Fügt eine kleine zufällige Schwankung hinzu (±0.5°C).
    """
    base_temp = TEMP_PROFILE.get(hour % 24, 18.0)
    variation = random.uniform(-0.5, 0.5)
    return round(base_temp + variation, 1)


def get_brightness_at_hour(hour: int) -> int:
    """
    Gibt den Helligkeitswert (0–100 %) für Lampen zur angegebenen Stunde zurück.
    0 = aus, 100 = volle Helligkeit.
    """
    return BRIGHTNESS_PROFILE.get(hour % 24, 0)


       # Beschreibung der Tageszeit 
def get_time_of_day(hour: int) -> str:
    
    if 5 <= hour < 9:
        return "Early Morning"
    elif 9 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 14:
        return "Midday"
    elif 14 <= hour < 18:
        return "Afternoon"
    elif 18 <= hour < 22:
        return "Evening"
    else:
        return "Night"


class DayEmulator:
    """
    Simuliert einen 24-Stunden-Tag für das Smart Home System.

    Parameter
    ----------
    database    : Database-Objekt aus main.py
    speed       : Sekunden pro simulierter Stunde (Standard: 1 Sekunde) Kann beliebig umgestellt werden
    start_hour  : Startstunde des Tages (0–23, Standard: 0)
    """

    def __init__(self, database, speed: float = 1.0, start_hour: int = 0):
        self.database = database
        self.speed = speed          
        self.current_hour = start_hour % 24
        self.current_temp = get_temperature_at_hour(self.current_hour)
        self.current_brightness = get_brightness_at_hour(self.current_hour)
        self.running = False
        self._log: list[dict] = []  # internes Protokoll aller Stunden

  

    def get_current_temperature(self) -> float:
        # Gibt die aktuelle simulierte Temperatur zurück.
        return self.current_temp

    def get_current_hour(self) -> int:
        # Gibt die aktuelle simulierte Stunde zurück.
        return self.current_hour

    def get_current_brightness(self) -> int:
        # Gibt den aktuellen Helligkeitswert (0–100 %) zurück.
        return self.current_brightness

    def get_log(self) -> list[dict]:
        # Gibt das vollständige Tagesprotokoll zurück.
        return self._log

    def simulate_day(self, on_hour_callback=None):
        """
        Startet die vollständige 24-Stunden-Simulation.

        Parameters
        ----------
        on_hour_callback : callable(hour, temperature, time_of_day, brightness) | None
            Wird jede simulierte Stunde aufgerufen. Kann genutzt werden,
            um z. B. Geräte automatisch zu schalten.
            Note: brightness (int, 0–100) is passed as a keyword argument.
        """
        self.running = True
        print("=" * 50)
        print("Smart Home – Day Simulation started")
        print("=" * 50)

        for hour in range(self.current_hour, 24):
            if not self.running:
                print("Simulation stopped.")
                break

            self.current_hour = hour
            self.current_temp = get_temperature_at_hour(hour)
            self.current_brightness = get_brightness_at_hour(hour)
            tod = get_time_of_day(hour)

            entry = {
                "hour": hour,
                "temperature": self.current_temp,
                "time_of_day": tod,
                "brightness": self.current_brightness,
            }
            self._log.append(entry)

            brightness_str = f"{self.current_brightness}%" if self.current_brightness > 0 else "OFF"
            print(
                f"\n[{hour:02d}:00 ]  {tod}  –  "
                f"Temperature: {self.current_temp}°C  |  "
                f"Lamp Brightness: {brightness_str}"
            )

            # Optionaler Callback aus der Main-Datei
            if callable(on_hour_callback):
                on_hour_callback(hour, self.current_temp, tod, brightness=self.current_brightness)

            # Warte 'speed' Sekunden bevor die nächste Stunde kommt
            time.sleep(self.speed)

        self.running = False
        print("\n" + "=" * 50)
        print("Day Simulation ended!")
        print("=" * 50)
        self._print_summary()

    def stop(self):
        # Stoppt die laufende Simulation vorzeitig.
        self.running = False

    def simulate_single_hour(self, hour: int = 0) -> dict:
        # Simuliert nur eine Stunde zum Testen
        if hour is None:
            hour = self.current_hour
        self.current_hour = hour % 24
        self.current_temp = get_temperature_at_hour(self.current_hour)
        self.current_brightness = get_brightness_at_hour(self.current_hour)
        tod = get_time_of_day(self.current_hour)
        entry = {
            "hour": self.current_hour,
            "temperature": self.current_temp,
            "time_of_day": tod,
            "brightness": self.current_brightness,
        }
        self._log.append(entry)
        return entry

   
    # Private helpers
   

    def _print_summary(self):
        if not self._log:
            return
        temps = [e["temperature"] for e in self._log]
        print(f"\n Daily review:")
        print(f"  Max. Temerature : {max(temps)}°C  (ca. {self._log[temps.index(max(temps))]['hour']:02d}:00)")
        print(f"  Min. Temperature : {min(temps)}°C  (ca. {self._log[temps.index(min(temps))]['hour']:02d}:00)")
        print(f"  Average Temperature : {round(sum(temps)/len(temps), 1)}°C")
        lit_hours = [e for e in self._log if e["brightness"] > 0]
        print(f"  Hours with lamps on : {len(lit_hours)} h")
        if lit_hours:
            avg_brightness = round(sum(e["brightness"] for e in lit_hours) / len(lit_hours), 1)
            print(f"  Average Lamp Brightness (when on) : {avg_brightness}%\n")
        else:
            print()



# Beispiel-Callback – kann 1:1 in main.py genutzt werden
''''MORGEN ENDPUNKTE FERTIG machen für Treshhold-Endpunkt '''

def default_device_callback(hub):
    """
    Liest Thresholds aus der rules-Tabelle.
    Temperatur steuert nur Heater, Brightness nur die Lampen.
    """

    def load_rules() -> dict:
        conn = hub.database.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rules")
        rows = cursor.fetchall()
        conn.close()
        return {row["device_id"]: row for row in rows}

    def handle_temperature(devices, temperature, rules):
        rule = rules.get("Heater")

        if rule:
            temp_high = rule["temp_treshold_high"]
            temp_low = rule["temp_treshold_low"]
        else:
            temp_high = 22.0
            temp_low = 16.0

        for device in devices:
            if device.device_type != "Heater":
                continue

            if temperature >= temp_high:
                device.turn_off()
                print(f"  [TEMP] {device.device_name} OFF  (>{temp_high}°C)")
            elif temperature <= temp_low:
                device.turn_on()
                print(f"  [TEMP] {device.device_name} ON   (<{temp_low}°C)")
            else:
                print(f"  [TEMP] {device.device_name} unchanged  ({temperature}°C)")

    def handle_brightness(devices, brightness, rules):
        rule = rules.get("Lamp")

        if rule:
            threshold = rule["brightness_treshold_high"]
        else:
            threshold = 10  # Default-Wert

        for device in devices:
            if device.device_type != "Lamp":
                continue

            if brightness >= threshold:
                device.turn_on()
                if hasattr(device, "set_brightness"):
                    device.set_brightness(brightness)
                print(f"  [LAMP] {device.device_name} ON  @ {brightness}%")
            else:
                device.turn_off()
                print(f"  [LAMP] {device.device_name} OFF  (<{threshold}%)")

    def callback(hour, temperature, time_of_day, brightness=0):
        rules = load_rules()
        print(f"\n  Stunde {hour:02d}:00 – {temperature}°C | Brightness: {brightness}%")
        handle_temperature(hub.devices, temperature, rules)
        handle_brightness(hub.devices, brightness, rules)

    return callback



# Standalone-Test für  Emulator ohne Main.py und Datenbank. über day_emulator.py aufrufbar


if __name__ == "__main__":
    print("Standalone-Test of simulator (No databank necessary)\n")
    emulator = DayEmulator(database=None, speed=0.2, start_hour=0)

    def simple_callback(hour, temp, tod, brightness=0):
        pass  # Nur Ausgabe, kein Hub

    emulator.simulate_day(on_hour_callback=simple_callback)