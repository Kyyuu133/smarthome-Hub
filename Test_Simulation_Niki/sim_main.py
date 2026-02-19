from Test_Simulation_Niki.sim_devices import Device, SmartHomeHub       # Imprtieren aus devices (Vorher Main)
from Test_Simulation_Niki.simulator import TimeCondition, Rule, DaySimulator  # importieren aus simulator
from datetime import time as dtime

# 1. Geräte erstellen
light = Device("Wohnzimmer Licht")
heater = Device("Heizung")
blinds = Device("Rollos")
coffee_mashine = Device("Kaffeemaschine")




# 2. Hub befüllen
hub = SmartHomeHub()
hub.add_device(light)
hub.add_device(heater)
hub.add_device(blinds)
hub.add_device(coffee_mashine)


# 3. Regeln definieren
regeln = [
    Rule(TimeCondition(dtime(8, 0),  dtime(9, 0)),  light,   "on"),
    Rule(TimeCondition(dtime(9, 0),  dtime(18, 0)), light,   "off"),
    Rule(TimeCondition(dtime(15, 0), dtime(23, 0)), light,   "on"),
    Rule(TimeCondition(dtime(6, 0),  dtime(22, 0)), heater, "on"),
    Rule(TimeCondition(dtime(13, 0), dtime(6, 0)),  heater, "off"),
    Rule(TimeCondition(dtime(7, 0),  dtime(9, 0)),  coffee_mashine,   "on"),
    Rule(TimeCondition(dtime(9, 0),  dtime(18, 0)), coffee_mashine,   "off"),
    Rule(TimeCondition(dtime(18, 0), dtime(23, 0)), blinds,   "on"),
    Rule(TimeCondition(dtime(6, 0),  dtime(22, 0)), blinds, "on"),
    Rule(TimeCondition(dtime(22, 0), dtime(6, 0)),  blinds, "off"),
    Rule(TimeCondition(dtime(12, 0),  dtime(9, 0)),  light,   "on"),
    Rule(TimeCondition(dtime(9, 0),  dtime(18, 0)), light,   "off"),
    Rule(TimeCondition(dtime(18, 0), dtime(23, 0)), light,   "on"),
    Rule(TimeCondition(dtime(6, 0),  dtime(22, 0)), heater, "on"),
    Rule(TimeCondition(dtime(18, 0), dtime(6, 0)),  heater, "off"),
]

# 4. Simulator starten
sim = DaySimulator(speed=2.0)
for regel in regeln:
    sim.add_rule(regel)

sim.run()



