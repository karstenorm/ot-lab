import logging
import time
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.server.sync import StartTcpServer
from pymodbus.constants import Defaults

"""
Coil 0 = manual cooling
HR 0 = temperature (0.1 C)
HR 1 = setpoint (0.1 C)
HR 2 = alarm
"""

log = logging.getLogger("plc")


class PLC:
    def __init__(self, process, ip="127.0.0.1", port=5020):
        self.ip = ip
        self.port = port

        self.process = process

        self.manual_cooling = 0
        self.setpoint = 350
        self.alarm = 0

        self.context = ModbusServerContext(
            slaves=ModbusSlaveContext(
                co=ModbusSequentialDataBlock(0, [self.manual_cooling] + [0] * 9),
                hr=ModbusSequentialDataBlock(0, [200, self.setpoint, self.alarm] + [0] * 97),
                zero_mode=True,
            ),
            single=True
        )

    def start_server(self):
        log.info(f"Starting Modbus Server on {self.ip}:{self.port}")

        Defaults.Timeout = 2
        StartTcpServer(context=self.context, address=(self.ip, self.port))

    def run(self):
        while True:
            setpoint = self.context[0x00].getValues(3, 1)[0]
            self.setpoint = max(200, min(setpoint, 500))

            self.manual_cooling = self.context[0x00].getValues(1, 0)[0]
            cooling = bool(self.manual_cooling)

            temperature = self.process.get_temperature()

            if not cooling and temperature > self.setpoint:
                cooling = True
            self.process.set_cooling(cooling)

            self.alarm = 1 if temperature > self.setpoint + 10 else 0

            self.context[0x00].setValues(3, 0, [temperature])
            self.context[0x00].setValues(3, 1, [self.setpoint])
            self.context[0x00].setValues(3, 2, [self.alarm])

            log.info(f"temp={temperature}, SP={self.setpoint}, ALM={self.alarm} coil={self.manual_cooling}")
            time.sleep(1)













