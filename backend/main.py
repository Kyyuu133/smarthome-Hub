


class SmartHomeHub:             # zum adden 
    def __init__(self):
        self.devices = []

    def add_device(self, device):
        self.devices.append(device)
        print(f"{device.name} was added to the hub.")

    def list_devices(self):
        print("Registered devices:")
        for device in self.devices:
            device.get_status()



class Device:
    def __init__(self, name):
        self.name = name
        self.is_on = False

    def turn_on(self):
        self.is_on = True
        print(f"{self.name} was turned ON")

    def turn_off(self):
        self.is_on = False
        print(f"{self.name} was turned OFF")

    def get_status(self):
        state = "ON" if self.is_on else "OFF"
        print(f"{self.name} is {state}.")