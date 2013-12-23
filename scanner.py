import bluetooth
import lightblue
import httplib
import re
import time
import threading
import copy

import basics
import devices

class Sighting:
    devices = []
    reportId = 0
    beginTime = ""

    def __init__(self, devices=[], reportId=1, beginTime=""):
        self.devices = copy.deepcopy(devices)
        self.reportId = reportId
        self.beginTime = beginTime

    def serialize(self):
        rootText = "xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns=\"urn:Mynamespace\""
        serial = "<?xml version=\"1.0\"?>"
        serial += "<sightings %s>" % rootText
        serial += "<clientReportId>%s</clientReportId>" % self.reportId
        serial += "<scanningBeginTime>%s</scanningBeginTime>" % basics.Clock().getIsoTime()
        serial += "<clientReportTime>%s</clientReportTime>" % basics.Clock().getIsoTime()
        serial += "<sightingItemsList>"
        for device in self.devices:
            serial += device.serialize(tagname='sightingItem')
        serial += "</sightingItemsList>"
        serial += "</sightings>"
        return serial
    
    def getNumDevices(self):
        return self.devices.__len__()
    
    def __repr__(self):
        st = "sighting("
        st += "reportId:%s," % self.reportId
        st += "beginTime:%s" % self.beginTime
        st += "devices:"
        for device in self.devices:
            st += str(device)
            st += " "
        st += ")"
        return st

    def __str__(self):
        return self.__repr__()


# -------------------------------------------------
class NameGetter(threading.Thread):
    def __init__(self, knownDevices, intrf):
        threading.Thread.__init__(self)
        self.cv = threading.Condition()
        self.kill_received = False
        self.knownDevices = knownDevices
        self.intrf = intrf
        self.addresses = {} # list of addresses to get name - {address:None}

    def run(self):
        self.cv.acquire()
        self.cv.wait()
        self.cv.release()
        while not self.kill_received:
            if self.addresses:
                devid = self.intrf.request(bandwidth=1)
                print "[SCN] getting names of %d devices using hci%s..." % (len(self.addresses), devid)
                try:
                    doneAddresses = {}
                    for addr in self.addresses:
                        #name = bluetooth.lookup_name(addr, device_id=devid)
                        name = bluetooth.lookup_name(addr)
                        self.knownDevices.setInfo(address=addr, name=name)
                        doneAddresses[addr] = name
                    self.cv.acquire()
                    for addr in doneAddresses:
                        if self.addresses.has_key(addr): self.addresses.pop(addr)
                    self.cv.release()
                    print "[SCN] inquiry ended. got the names of %d devices" % len(doneAddresses), doneAddresses
                except bluetooth.btcommon.BluetoothError:
                    #raise bluetooth.btcommon.BluetoothError
                    print "[SCN] bluetooth error"
                    time.sleep(1)
                self.intrf.release(interface=devid, bandwidth=1)
            else:
                #print "[SCN] there are no devices to get its names"
                self.cv.acquire()
                self.cv.wait()
                self.cv.release()
        #print "[SCN] NameGetter thread ended"

    def kill(self):
        #print "[SCN] killing NameGetter thread..."
        if(self.isAlive):
            self.kill_received = True
            self.cv.acquire()
            self.cv.notify()
            self.cv.release()

    def addAddresses(self, addresses=[]):
        self.cv.acquire()
        for addr in addresses:
            self.addresses[addr] = None
        self.cv.notify()
        self.cv.release()


# -------------------------------------------------
class ServiceGetter(threading.Thread):
    def __init__(self, knownDevices, intrf):
        threading.Thread.__init__(self)
        self.cv = threading.Condition()
        self.kill_received = False
        self.knownDevices = knownDevices
        self.intrf = intrf
        self.addresses = {} # list of addresses to get name - {address:None}

    def run(self):
        self.cv.acquire()
        self.cv.wait()
        self.cv.release()
        while not self.kill_received:
            if self.addresses:
                devid = self.intrf.request(bandwidth=1)
                print "[SCN] getting services of %d devices using hci%s..." % (len(self.addresses), devid)
                try:
                    doneAddresses = {}
                    for addr in self.addresses:
                        services = lightblue.findservices(addr)
                        services2 = {}
                        for serv in services:
                            services2[serv[1]] = serv[2]
                        self.knownDevices.setInfo(address=addr, services=services2)
                        doneAddresses[addr] = services2
                    self.cv.acquire()
                    for addr in doneAddresses:
                        if self.addresses.has_key(addr): self.addresses.pop(addr)
                    self.cv.release()
                    print "[SCN] inquiry ended. got the services of %d devices" % len(doneAddresses), doneAddresses
                except bluetooth.btcommon.BluetoothError:
                    #raise bluetooth.btcommon.BluetoothError
                    print "[SCN] bluetooth error"
                    time.sleep(1)
                self.intrf.release(interface=devid, bandwidth=1)
            else:
                #print "there are no devices to get its services"
                self.cv.acquire()
                self.cv.wait()
                self.cv.release()
        #print "[SCN] ServiceGetter thread ended"

    def kill(self):
        #print "[SCN] killing ServiceGetter thread..."
        if(self.isAlive):
            self.kill_received = True
            self.cv.acquire()
            self.cv.notify()
            self.cv.release()

    def addAddresses(self, addresses=[]):
        self.cv.acquire()
        for addr in addresses:
            self.addresses[addr] = None
        self.cv.notify()
        self.cv.release()



# -------------------------------------------------
class Scanner(threading.Thread):    
    def __init__(self, sched, intrf):
        threading.Thread.__init__(self)
        self.cv = threading.Condition()
        self.kill_received = False
        self.sched = sched
        self.intrf = intrf
        self.scannerOn = False
        self.knownDevices = devices.ListOfDevices()
        self.numErrors = 0
        self.numErrorsUntilReset = 15 # workaround for OpenWrt's bug :(
        self.lastScanTimestamp = 0
        
        self.scaninterval=30
        self.getnames=False
        #self.namechache=None
        self.getservices=False
        #self.scantimeout=None
        #self.nametimeout=None
        #self.servicetimeout=None

    def run(self):
        print "[SCN] Scanner thread running"
        namegetter = NameGetter(self.knownDevices, self.intrf)
        servicegetter = ServiceGetter(self.knownDevices, self.intrf)
        namegetter.start()
        servicegetter.start()
        while not self.kill_received:
            if self.scannerOn:
                devid = self.intrf.request(bandwidth=8)
                (status,seenaddresses) = self._doScan(devid=devid)
                addressesToGetName = []
                addressesToGetServices = []
                for addr in seenaddresses:
                    self.knownDevices.add(addr)
                    dev = self.knownDevices.getDeviceByAddress(addr)
                    
                    # run the getter threads:
                    if self.namechache and self.namechache > 0:
                            timeWithNameInCache = self.namechache
                    else:
                            timeWithNameInCache = 0
                    if self.getnames and dev and (not dev.name or dev.lastNameUpdate < basics.Clock().getTimestamp() - timeWithNameInCache):
                        addressesToGetName.append(addr)
                    if self.getservices and dev and not dev.services:
                        addressesToGetServices.append(addr)
                self.intrf.release(interface=devid, bandwidth=8)

                # create the sighting structure and register event
                seendevices2 = []
                for addr in seenaddresses:
                    seendevices2.append(self.knownDevices.getDeviceByAddress(addr))
                sighting = Sighting(seendevices2)
                if(status>0): self.sched.pushEvent("newscan",sighting)

                namegetter.addAddresses(addressesToGetName)
                #namegetter.join()
                servicegetter.addAddresses(addressesToGetServices)
                #servicegetter.join()
                wait = self.scaninterval - (time.time() - self.lastScanTimestamp)
                if wait < -100000 or wait > self.scaninterval:
                    wait = self.scaninterval
                if wait>0:
                    wait = int(round(wait))
                    print "[SCN] waiting %d seconds until scanning again (scaninterval=%s)" % (wait, self.scaninterval)
                    for i in range(wait):
                        if self.kill_received: break
                        time.sleep(1)
            else:
                self.cv.acquire()
                self.cv.wait()
                self.cv.release()
        namegetter.kill()
        servicegetter.kill()
        print "[SCN] Scanner thread ended"

    def kill(self):
        if self.scannerOn: text = "scannings are still being performed! please wait..."
        else: text = ""
        print "[SCN] killing Scanner thread...", text
        if(self.isAlive):
            self.kill_received = True
            self.cv.acquire()
            self.cv.notify()
            self.cv.release()

    def _doScan(self, devid=-1):
        status = 0
        seenaddresses = []
        try:
            if self.lastScanTimestamp: print "[SCN] last scan was performed %.2f seconds ago" % round(time.time() - self.lastScanTimestamp, 2)
            self.lastScanTimestamp = time.time()
            try: # try to use a specific Bluetooth interface:
                print "[SCN] address scanning using hci%s..." % devid
                seenaddresses = bluetooth.discover_devices(device_id=devid)
            except TypeError: # if there is no support for multiple interfaces, use the default one:
                print "[SCN] address scanning using default interface (no support for multiple interfaces)"
                seenaddresses = bluetooth.discover_devices()
            status = seenaddresses.__len__()
            print "[SCN] done. took %.2f sec. seen addresses:" % (round(time.time() - self.lastScanTimestamp, 2)), seenaddresses
            self.numErrors = 0
        except bluetooth.btcommon.BluetoothError: # if an error occurs, try to recover
            status = -1
            self.numErrors += 1
            print "[SCN] bluetooth error (%d of %d tolerated)" % (self.numErrors, self.numErrorsUntilReset)
            if self.numErrors == self.numErrorsUntilReset+1:
                print "[SCN] BT ERROR: Resetting interface hci%d" % devid
                basics.Exec().execlp('hciconfig', ['hci'+str(devid), 'down'], wait=True)
            elif self.numErrors == self.numErrorsUntilReset+3:
                print "[SCN] BT ERROR: Critical, restarting hotspot :("
                #basics.Exec().execlp('reboot')
        return (status, seenaddresses)

    def startScanning(self, scaninterval=30, getnames=False, namechache=None, getservices=False, scantimeout=None, nametimeout=None, servicetimeout=None):
        self.cv.acquire()
        self.scaninterval = scaninterval
        self.getnames = getnames
        self.namechache = namechache
        self.getservices = getservices
        self.scantimeout = scantimeout
        self.nametimeout = nametimeout
        self.servicetimeout = servicetimeout
        self.scannerOn = True
        self.cv.notify()
        self.cv.release()
        pass

    def stopScanning(self):
        self.cv.acquire()
        self.scannerOn = False
        self.cv.notify()
        self.cv.release()
        pass

