# OT-lab

A simple OT/ICS lab project that simulates a temperature control process with a PLC and a HMI.

## Components
- **Process**: simulates a heating/cooling process
- **PLC**: exposes Modbus registers and controls the process
- **HMI**: PyQt-based interface for monitoring and manual control

## Modbus Mapping
- **Coil 0** = manual cooling
- **HR 0** = temperature (0.1 °C)
- **HR 1** = setpoint (0.1 °C)
- **HR 2** = alarm

## Run
```bash
python main.py
python hmi.py
```
