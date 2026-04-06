import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QSpinBox, QCheckBox, QFrame, QTextEdit
)
from PyQt6.QtCore import QTimer, Qt
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.exceptions import ConnectionException
from datetime import datetime


class HMI(QWidget):
    def __init__(self, ip="127.0.0.1", port=5020):
        super().__init__()

        self.alarm_active = None

        self.setWindowTitle("HMI")
        self.setGeometry(400, 200, 600, 450)

        self.title = QLabel("Cooling Circuit Overview")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size: 18px; color: lightgrey;")

        # temperature label
        self.temp_label = QLabel("Temp: -- °C")
        self.temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # alarm indicator
        self.status_label = QLabel("Status: --")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("background-color: grey; color: white;")

        # mode label
        self.mode_label = QLabel("Mode: --")
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode_label.setMinimumWidth(140)
        self.mode_label.setStyleSheet("background-color: rgb(70,70,70); color: white;")

        self.setpoint_label = QLabel("Setpoint:")

        # setpoint input
        self.setpoint_input = QSpinBox()
        self.setpoint_input.setRange(20, 50)
        self.setpoint_btn = QPushButton("Set new setpoint")

        # coil cooling checkbox
        self.cooling_checkbox = QCheckBox("Manual cooling ON")

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumWidth(400)

        self.main_layout = QHBoxLayout()
        self.controls_layout = QVBoxLayout()

        self.make_layout()

        # timer for polling
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(1000)
        self.poll_timer.timeout.connect(self.update_values)

        self.client = ModbusTcpClient(ip, port)
        self.connected = False

        # timer for connecting
        self.connect_timer = QTimer(self)
        self.connect_timer.setInterval(2000)
        self.connect_timer.timeout.connect(self.try_connect)
        self.connect_timer.start()

        # button events
        self.setpoint_btn.clicked.connect(self.set_setpoint)
        self.cooling_checkbox.clicked.connect(self.set_cooling)

    def make_layout(self):
        self.controls_layout.addWidget(self.title)
        self.controls_layout.addWidget(self._add_separator())
        self.controls_layout.addWidget(self.temp_label)
        self.controls_layout.addWidget(self.status_label)
        self.controls_layout.addWidget(self._add_separator())
        self.controls_layout.addWidget(self.cooling_checkbox, alignment=Qt.AlignmentFlag.AlignCenter)

        bottom_layout = QVBoxLayout()
        bottom1 = QHBoxLayout()
        bottom1.addWidget(self.mode_label)

        bottom1.addWidget(self.setpoint_label)
        bottom1.addWidget(self.setpoint_input)
        bottom1.addWidget(self.setpoint_btn)

        bottom_layout.addLayout(bottom1)
        self.controls_layout.addLayout(bottom_layout)

        self.main_layout.addLayout(self.controls_layout)
        self.main_layout.addWidget(self.log_box)
        self.setLayout(self.main_layout)

    def log_event(self, message: str):
        self.log_box.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] : {message}")

    def try_connect(self):
        connect = self.client.connect()

        if not connect:
            self.connected = False
            return

        if not self.connected:
            self.connected = True
            self.set_online()

    def set_online(self):
        self.log_event("PLC connected")
        self.connect_timer.stop()
        self.poll_timer.start()
        self.setpoint_input.setEnabled(True)
        self.setpoint_btn.setEnabled(True)
        self.cooling_checkbox.setEnabled(True)

    def set_offline(self):
        if not self.connected and not self.poll_timer.isActive():
            return

        self.connected = False
        self.log_event("PLC disconnected")
        self.poll_timer.stop()
        self.connect_timer.start()
        self.temp_label.setText("Temp: -- °C")
        self.status_label.setText("Status: --")
        self.status_label.setStyleSheet("background-color: grey; color: white;")
        self.mode_label.setText("Mode: --")
        self.setpoint_input.setEnabled(False)
        self.setpoint_btn.setEnabled(False)
        self.cooling_checkbox.setEnabled(False)
        self.alarm_active = None

    def update_values(self):
        try:
            registers = self.client.read_holding_registers(0, 3, unit=0x00)
            if registers.isError():
                self.set_offline()
                return

            temperature = registers.registers[0]
            setpoint = registers.registers[1]
            alarm_value = registers.registers[2]

            self.temp_label.setText(f"Temp: {temperature / 10} °C")

            self.setpoint_input.blockSignals(True)
            self.setpoint_input.setValue(setpoint // 10)
            self.setpoint_input.blockSignals(False)

            alarm_active = bool(alarm_value)
            if alarm_active != self.alarm_active:
                self.alarm_active = alarm_active
                self.update_alarm_display(alarm_active)

            coil = self.client.read_coils(0, 1, unit=0x00)
            if coil.isError():
                self.set_offline()
                return

            manual_cooling = coil.bits[0]
            self.cooling_checkbox.blockSignals(True)
            self.cooling_checkbox.setChecked(manual_cooling)
            self.cooling_checkbox.blockSignals(False)

            self.update_mode_display(manual_cooling)

        except ConnectionException:
            self.set_offline()

    def set_setpoint(self):
        if not self.connected:
            return

        setpoint = self.setpoint_input.value()
        result = self.client.write_register(1, setpoint * 10, unit=0x00)

        if result.isError():
            self.log_event(f"[ERROR] Could not send setpoint")
        else:
            self.log_event(f"SETPOINT = {setpoint}")

    def set_cooling(self):
        cooling = self.cooling_checkbox.isChecked()
        self.cooling_checkbox.setStyleSheet("color: green;" if cooling else "color: gray;")

        if self.connected:
            result = self.client.write_coil(0, cooling, unit=0x00)
            if result.isError():
                self.log_event(f"[ERROR] Could not send cooling")
            else:
                self.log_event(f"COOLING = {int(cooling)}")

    def update_alarm_display(self, alarm_active: bool):
        if alarm_active:
            self.log_event(f"TEMP_ALARM = 1")
            self.status_label.setText("Status: ALARM")
            self.status_label.setStyleSheet("background-color: red; color: white;")
        else:
            self.log_event(f"TEMP_ALARM = 0")
            self.status_label.setText("Status: OK")
            self.status_label.setStyleSheet("background-color: green; color: white;")

    def update_mode_display(self, manual_cooling: bool):
        mode = "MANUAL" if manual_cooling else "AUTO"
        self.mode_label.setText(f"Mode: {mode}")

    def _add_separator(self):
        separator = QFrame()
        separator.setStyleSheet("background-color: gray;")
        separator.setFixedHeight(1)
        return separator

    def closeEvent(self, event):
        self.poll_timer.stop()
        self.connect_timer.stop()
        self.client.close()
        super().closeEvent(event)


def run():
    app = QApplication(sys.argv)

    base_dir = Path(__file__).parent
    qss_path = base_dir / "ui" / "hmi.qss"

    try:
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"Warning: QSS file not found at {qss_path}")

    window = HMI("127.0.0.1", 5020)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
