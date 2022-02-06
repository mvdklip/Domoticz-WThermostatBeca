# WThermostatBeca Python Plugin for Domoticz
#
# Authors: mvdklip
#
# Based on
#
# https://github.com/fashberg/WThermostatBeca#json-structures

"""
<plugin key="WThermostatBeca" name="WThermostatBeca" author="mvdklip" version="1.2.0">
    <description>
        <h2>WThermostatBeca Plugin</h2><br/>
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Integrate a BHT thermostat running the WThermostatBeca firmware</li>
        </ul>
    </description>
    <params>
        <param field="Address" label="IP Address" width="200px" required="true"/>
        <param field="Port" label="Port" width="30px" required="true" default="80"/>
        <param field="Mode3" label="Query interval" width="75px" required="true">
            <options>
                <option label="5 sec" value="5" default="true"/>
                <option label="15 sec" value="15"/>
                <option label="30 sec" value="30"/>
                <option label="1 min" value="60"/>
                <option label="3 min" value="180"/>
                <option label="5 min" value="300"/>
                <option label="10 min" value="600"/>
            </options>
        </param>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true"/>
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz
import json


class BasePlugin:
    enabled = False
    lastPolled = 0
    pendingRequests = []
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    httpConn = None
    numConnectErrors = 0
    maxConnectErrors = 5
    backoffState = False
    backoffTime = 60

    def __init__(self):
        return

    def onStart(self):
        Domoticz.Debug("onStart called")
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
        else:
            Domoticz.Debugging(0)

        if len(Devices) < 1:
            Domoticz.Device(Name="Switch", Unit=1, TypeName='Switch', Image=9).Create()
        if len(Devices) < 2:
            Domoticz.Device(Name="Temperature", Unit=2, TypeName='Temperature').Create()
        if len(Devices) < 3:
            Domoticz.Device(Name="Setpoint", Unit=3, Type=242, Subtype=1).Create()

        DumpConfigToLog()

        self.httpConn = Domoticz.Connection(Name="HTTP Connection", Transport="TCP/IP", Protocol="HTTP", Address=Parameters["Address"], Port=Parameters["Port"])

        Domoticz.Heartbeat(1)

    def onStop(self):
        Domoticz.Debug("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")

        if (Status == 0):
            self.numConnectErrors = 0
            Domoticz.Debug("Connected to %s:%s." % (Parameters["Address"], Parameters["Port"]))
            HandlePendingRequests(self, Connection)
        else:
            self.numConnectErrors += 1
            Domoticz.Log("Failed to connect #%d to %s:%s with status %d, error %s" % (self.numConnectErrors, Parameters["Address"], Parameters["Port"], Status, Description))
            if (self.numConnectErrors >= self.maxConnectErrors):
                Domoticz.Error("Tried %d times to connect to %s:%s. Backing off..." % (self.numConnectErrors, Parameters["Address"], Parameters["Port"]))
                self.backoffState = True
                self.lastPolled = 1

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")

        # device can only process one http request per connection; disconnect for next request
        Connection.Disconnect()

        Status = int(Data["Status"])
        if (Status == 200):
            Domoticz.Debug("Good response received from %s:%s." % (Parameters["Address"], Parameters["Port"]))
            if "Data" in Data:
                strData = Data["Data"].decode("utf-8", "ignore")
                try:
                    j = json.loads(strData)
                except Exception as e:
                    Domoticz.Error("No JSON data from %s:%s; %s." % (Parameters["Address"], Parameters["Port"], e))
                else:
                    Domoticz.Debug("Received JSON data: %s." % j)
                    if 'deviceOn' in j:
                        newValue = int(j['deviceOn'])
                        if newValue != Devices[1].nValue:
                            Devices[1].Update(nValue=newValue, sValue="")
                    if 'temperature' in j:
                        Devices[2].Update(nValue=0, sValue=str(j['temperature']))
                    if 'targetTemperature' in j:
                        newValue = str(j['targetTemperature'])
                        if newValue != Devices[3].sValue:
                            Devices[3].Update(nValue=0, sValue=newValue)
        else:
            Domoticz.Error("Bad response (%d) received from %s:%s." % (Status, Parameters["Address"], Parameters["Port"]))

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for unit %d with command %s, level %s." % (Unit, Command, Level))

        if (Unit == 1) and (Command == "On"):
            SetDeviceProperty(self, 'deviceOn', True)
            if (self.backoffState):
                Devices[1].Update(nValue=1, sValue="")
        elif (Unit == 1) and (Command == "Off"):
            SetDeviceProperty(self, 'deviceOn', False)
            if (self.backoffState):
                Devices[1].Update(nValue=0, sValue="")
        elif (Unit == 3) and (Command == "Set Level"):
            SetDeviceProperty(self, 'targetTemperature', Level)
            if (self.backoffState):
                Devices[3].Update(nValue=0, sValue=str(Level))

        return True

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called %d %d" % (self.lastPolled, self.backoffState))

        if self.lastPolled == 0:
            if self.backoffState:
                self.pendingRequests.clear()
                self.numConnectErrors = 0
                self.backoffState = False
            elif len(self.pendingRequests) == 0:
                GetDeviceProperties(self)

        HandlePendingRequests(self, self.httpConn)

        self.lastPolled += 1
        if self.backoffState:
            self.lastPolled %= self.backoffTime
        else:
            self.lastPolled %= int(Parameters["Mode3"])


global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()


# Generic helper functions
def HandlePendingRequests(plugin, conn):
    if conn is not None:
        if len(plugin.pendingRequests) > 0:
            Domoticz.Debug("Pending requests: %d, Connecting: %d, Connected: %d" % (len(plugin.pendingRequests), conn.Connecting(), conn.Connected()))
            if conn.Connected():
                r = plugin.pendingRequests.pop(0)
                Domoticz.Debug("Connected to %s:%s. Sending pending request %s %s." % (Parameters["Address"], Parameters["Port"], r["Verb"], r["URL"]))
                conn.Send(r)
            elif conn.Connecting():
                Domoticz.Debug("Waiting for connection to %s:%s." % (Parameters["Address"], Parameters["Port"]))
            elif plugin.numConnectErrors < plugin.maxConnectErrors:
                Domoticz.Debug("Not connected. Connecting to %s:%s." % (Parameters["Address"], Parameters["Port"]))
                conn.Connect()
#        elif conn.Connected():
#            Domoticz.Debug("Connected to %s:%s but no pending requests. Disconnecting." % (Parameters["Address"], Parameters["Port"]))
#            conn.Disconnect()

def GetDeviceProperties(plugin):
    url = "/things/thermostat/properties/"
    Domoticz.Debug("Getting device properties from %s" % url)
    plugin.pendingRequests.append({'Verb':'GET', 'URL':url, "Headers":plugin.headers})

def SetDeviceProperty(plugin, propName, propValue):
    url = "/things/thermostat/properties/%s" % propName
    data = { propName: propValue }
    Domoticz.Debug("Setting device property at %s to: %s" % (url, data))
    plugin.pendingRequests.append({'Verb':'PUT', 'URL':url, "Headers":plugin.headers, "Data":json.dumps(data)})

def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
