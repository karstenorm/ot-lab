import threading
import time


class Process:
    def __init__(self):
        self._lock = threading.Lock()

        self.temperature = 200
        self.cooling = False
        self.cooling_force = 5

        self.min_temperature = 200
        self.max_temperature = 1000
        self.heating_rate = 10

    def set_cooling(self, cooling: bool):
        with self._lock:
            self.cooling = cooling

    def get_temperature(self) -> int:
        with self._lock:
            return self.temperature

    def update(self):
        with self._lock:
            if self.cooling:
                self.temperature -= self.cooling_force
            else:
                self.temperature += self.heating_rate

            self.temperature = max(
                min(self.temperature, self.max_temperature),
                self.min_temperature
            )

    def run(self):
        while True:
            self.update()
            time.sleep(1)


