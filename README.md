# Domoticz-WThermostatBeca
Domoticz plugin to integrate a BHT thermostat running WThermostatBeca firmware

Tested with Python version 3.8, Domoticz version 2020.2

## Prerequisites

BHT-002, BHT-3000 or BHT-6000 thermostat running the WThermostatBeca firmware from https://github.com/fashberg/WThermostatBeca or https://github.com/klausahrenberg/WThermostatBeca.

## Installation

Assuming that domoticz directory is installed in your home directory.

```bash
cd ~/domoticz/plugins
git clone https://github.com/mvdklip/Domoticz-WThermostatBeca
# restart domoticz:
sudo /etc/init.d/domoticz.sh restart
```
In the web UI, navigate to the Hardware page and add an entry of type "WThermostatBeca".

Make sure to (temporarily) enable 'Accept new Hardware Devices' in System Settings so that the plugin can add devices.

Afterwards navigate to the Devices page and enable the newly created devices.

## Updating

Like other plugins, in the Domoticz-WThermostatBeca directory:
```bash
git pull
sudo /etc/init.d/domoticz.sh restart
```

## Parameters

| Parameter | Value |
| :--- | :--- |
| **IP address** | IP of the thermostat eg. 192.168.1.231 |
| **Port** | Port of the thermostat web interface eg. 80 |
| **Query interval** | how often is data retrieved |
| **Debug** | show debug logging |

## Acknowledgements

Based on

https://github.com/fashberg/WThermostatBeca#json-structures
