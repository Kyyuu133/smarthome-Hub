import time
from datetime import datetime, timedelta, time as dtime
from Niki_Test.devices import Device, SmartHomeHub   # nimmt die Klassen aus devices (Main)


class TimeCondition:
    def __init__(self, start: dtime, end: dtime):
        self.start = start
        self.end = end

    def check(self, current_time) -> bool:
        if self.start <= self.end:
            return self.start <= current_time <= self.end
        return current_time >= self.start or current_time <= self.end  # über Mitternacht


class Rule: # Rollen erstellen mit Zeitstempel, Gerätname und An oder Aus
    def __init__(self, condition: TimeCondition, device: Device, action: str):
        self.condition = condition
        self.device = device
        self.action = action

    def evaluate(self, current_time): # Nur an oder ausschalten, wenn das gegenteil aktiv ist 
        if self.condition.check(current_time):
            if self.action == "on" and not self.device.is_on:
                self.device.turn_on()
            elif self.action == "off" and self.device.is_on:
                self.device.turn_off()


class DaySimulator:
    def __init__(self, speed: float = 1.0): # Geschwindigkeit einstellen in Float
        self.speed = speed
        self.rules = []

    def add_rule(self, rule: Rule):
        self.rules.append(rule)

    def run(self):
        start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        print("\n" + "="*40)
        print("DAY-SIMULATION STARTING")
        print("="*40)

        for minutes in range(0, 24 * 60, 15):
            sim_time = start + timedelta(minutes=minutes)
            current  = sim_time.time()

            print(f"\n{sim_time.strftime('%H:%M')} Uhr")

            for rule in self.rules:
                rule.evaluate(current)

            time.sleep(self.speed / 4)

        print("\n" + "="*40)
        print("SAY-SIMULATION ENDED")
        print("="*40)