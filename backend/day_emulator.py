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


def get_temperature_at_hour(hour: int) -> float:
    """
    Gibt die simulierte Temperatur für eine bestimmte Stunde zurück.
    Fügt eine kleine zufällige Schwankung hinzu (±0.5°C).
    """
    base_temp = TEMP_PROFILE.get(hour % 24, 18.0)
    variation = random.uniform(-0.5, 0.5)
    return round(base_temp + variation, 1)

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
    speed       : Sekunden pro simulierter Stunde (Standard: 1 Sekunde)
    start_hour  : Startstunde des Tages (0–23, Standard: 0)
    """

    def __init__(self, database, speed: float = 1.0, start_hour: int = 0):
        self.database = database
        self.speed = speed          
        self.current_hour = start_hour % 24
        self.current_temp = get_temperature_at_hour(self.current_hour)
        self.running = False
        self._log: list[dict] = []  # internes Protokoll aller Stunden

  

    def get_current_temperature(self) -> float:
        # Gibt die aktuelle simulierte Temperatur zurück.
        return self.current_temp

    def get_current_hour(self) -> int:
        # Gibt die aktuelle simulierte Stunde zurück.
        return self.current_hour

    def get_log(self) -> list[dict]:
        # Gibt das vollständige Tagesprotokoll zurück.
        return self._log

    def simulate_day(self, on_hour_callback=None):
        """
        Startet die vollständige 24-Stunden-Simulation.

        Parameters
        ----------
        on_hour_callback : callable(hour, temperature, time_of_day) | None
            Wird jede simulierte Stunde aufgerufen. Kann genutzt werden,
            um z. B. Geräte automatisch zu schalten.
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
            tod = get_time_of_day(hour)

            entry = {
                "hour": hour,
                "temperature": self.current_temp,
                "time_of_day": tod,
            }
            self._log.append(entry)

            print(f"\n[{hour:02d}:00 ]  {tod}  –  Temperature: {self.current_temp}°C")

            # Optionaler Callback aus der Main-Datei
            if callable(on_hour_callback):
                on_hour_callback(hour, self.current_temp, tod)

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
        tod = get_time_of_day(self.current_hour)
        entry = {"hour": self.current_hour, "temperature": self.current_temp, "time_of_day": tod}
        self._log.append(entry)
        return entry

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _print_summary(self):
        if not self._log:
            return
        temps = [e["temperature"] for e in self._log]
        print(f"\n Daily review:")
        print(f"  Max. Temerature : {max(temps)}°C  (ca. {self._log[temps.index(max(temps))]['hour']:02d}:00)")
        print(f"  Min. Temperature : {min(temps)}°C  (ca. {self._log[temps.index(min(temps))]['hour']:02d}:00)")
        print(f"  Average Temperature : {round(sum(temps)/len(temps), 1)}°C\n")


# ----------------------------------------------------------------------
# Beispiel-Callback – kann 1:1 in main.py genutzt werden
# ----------------------------------------------------------------------

def default_device_callback(hub, temp_threshold_high=22.0, temp_threshold_low=16.0):
    """
    Gibt einen vorkonfigurierten Callback zurück, der Geräte automatisch
    ein-/ausschaltet basierend auf der Temperatur.

    Nutzung in main.py:
        callback = default_device_callback(hub)
        emulator.simulate_day(on_hour_callback=callback)
    """
    def callback(hour, temperature, time_of_day):
        print(f"Automatic-Check: {temperature}°C", end="  ")
        if temperature >= temp_threshold_high:
            print("(high ->  Heizung AUS)")
            for device in hub.devices:
                if "Climate" in device.device_name.lower() or "ac" in device.device_name.lower():
                    device.turn_on()
                if "heater" in device.device_name.lower() or "heater" in device.device_name.lower():
                    device.turn_off()
        elif temperature <= temp_threshold_low:
            print("(niedrig → Heizung AN, Klimaanlage AUS)")
            for device in hub.devices:
                if "heizung" in device.device_name.lower() or "heater" in device.device_name.lower():
                    device.turn_on()
                if "klima" in device.device_name.lower() or "ac" in device.device_name.lower():
                    device.turn_off()
        else:
            print("(normal → keine Änderung)")

        # Lichter: nachts/morgens an, tagsüber aus
        if hour < 7 or hour >= 21:
            for device in hub.devices:
                if "licht" in device.device_name.lower() or "light" in device.device_name.lower() or "lampe" in device.device_name.lower():
                    device.turn_on()
        else:
            for device in hub.devices:
                if "licht" in device.device_name.lower() or "light" in device.device_name.lower() or "lampe" in device.device_name.lower():
                    device.turn_off()

    return callback


# ----------------------------------------------------------------------
# Standalone-Test (python day_emulator.py)
# ----------------------------------------------------------------------

if __name__ == "__main__":
    print("Standalone-Test of simulator (No databank necessary)\n")
    emulator = DayEmulator(database=None, speed=0.2, start_hour=0)

    def simple_callback(hour, temp, tod):
        pass  # Nur Ausgabe, kein Hub

    emulator.simulate_day(on_hour_callback=simple_callback)