import threading
import basics
import re

class Device:
    address = "" # xx:xx:xx:xx:xx:xx
    name = "" # string
    devclass = "" # string
    services = {} # {channel:value}
    lastSeen = 0 # timestamp
    lastNameUpdate = 0 # timestamp

    def __init__(self, address="", name="", devclass="Unknown", services={}, lastSeen=0):
        self.address = address
        self.name = name
        self.devclass = devclass
        self.services = services
        self.lastSeen = lastSeen
        if self.name: self.lastNameUpdate = basics.Clock().getTimestamp()
        else: self.lastNameUpdate = 0
        if self.services: self.lastServicesUpdate = basics.Clock().getTimestamp()
        else: self.lastServicesUpdate = 0
    
    def _stripSeparators(self, address):
        p = re.compile(r':')
        return p.sub("",address)

    def addService(self, channel, name):
        self.services[channel] = name
        self.lastServicesUpdate = basics.Clock().getTimestamp()

    def getServiceName(self, channel):
        if self.services.has_key(channel):
            return self.services[channel]
        else:
            return None

    def getServiceChannel(self, name):
        for channel in self.services:
            #if i[1] == name: return i[0]
            if self.services[channel] == name: return channel
        return None

    def serialize(self, tagname="device"):
        serial = ""
        serial += "<%s>" % tagname
        serial += "<deviceName>%s</deviceName>" % self.name
        serial += "<deviceAddress>%s</deviceAddress>" % self._stripSeparators(self.address)
        serial += "<deviceClass>%s</deviceClass>" % self.devclass
        serial += "<isAuthenticated>true</isAuthenticated>"
        serial += "<isConnected>true</isConnected>"
        serial += "</%s>" % tagname
        return serial

    def __repr__(self):
        dev = "device(address:%s," % self.address
        dev += "name:%s," % self.name
        dev += "devclass:%s," % self.devclass
        dev += "lastSeen:%s," % self.lastSeen
        dev += "services:"
        dev += str(self.services)
        dev += ")"
        return dev

    def __str__(self):
        return self.__repr__()



# --------------------------------------------
class ListOfDevices():

    def __init__(self):
        self._listOfDevices = {} # {address:Device}

    def add(self, address):
        if not self._listOfDevices.has_key(address): self._listOfDevices[address] = Device(address=address)
    
    def setInfo(self, address, name="", devclass=None, services={}, lastSeen=0): # if device is not on the list, this method adds it
        if not self._listOfDevices.has_key(address): self._listOfDevices[address] = Device(address=address)
        if name:
            self._listOfDevices[address].name = name
            self._listOfDevices[address].lastNameUpdate = basics.Clock().getTimestamp()
        if devclass: self._listOfDevices[address].devclass = devclass
        if services: self._listOfDevices[address].services = services
        if lastSeen: self._listOfDevices[address].lastseen = lastSeen

    def getDeviceByAddress(self, address):
        if self._listOfDevices.has_key(address): return self._listOfDevices[address]
        else: None

    def list(self):
        #devices = []
        #for dev in self._listOfDevices:
        #    devices.append(dev)
        #return devices
        return self._listOfDevices

    def __repr__(self):
        st = ""
        for i in self._listOfDevices.keys():
            st += i
            st += ":"
            st += self._listOfDevices[i].name
            st += ", "
        return st

    def __str__(self):
        return self.__str__()


