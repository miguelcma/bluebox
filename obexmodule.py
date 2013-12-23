import httplib
import socket
import lightblue
import re
import hashlib
import time
import threading

import basics
import resources

class ObexReceive(threading.Thread):
    advertising = False

    def __init__(self, sched, intrf):
        threading.Thread.__init__(self)
        self.cv = threading.Condition()
        self.kill_received = False
        self.sched = sched
        self.intrf = intrf
        self.devid = 0

    def run(self):
        print "[OXR] ObexReceive thread running"
        clock = basics.Clock()
        while not self.kill_received:
            if self.advertising:
                addr = None
                filename = "/tmp/bluebox-" + (hashlib.md5("11:11:11"+str(clock.getMicroTimestamp())).hexdigest())
                print "[OXR] Ready to receive a file (%s) on interface hci%d" % (filename, self.devid)
                addr = lightblue.obex.recvfile(self.obexsocket, filename)
                print "[OXR] File",filename,"received from device", addr, ":)"
                self.sched.pushEvent("obexin",[filename,addr])
                time.sleep(1)
            else:
                self.cv.acquire()
                self.cv.wait()
                self.cv.release()
        print "[OXR] ObexReceiver thread ended"

    def kill(self):
        print "[OXR] killing ObexReceiver thread..."
        if(self.isAlive):
            self.kill_received = True
            self.cv.acquire()
            self.cv.notify()
            self.cv.release()
    
    def startAdvertising(self):
        self.cv.acquire()
        if not self.advertising:
            self.devid = self.intrf.request(bandwidth=0)
            self.obexsocket = lightblue.socket()
            self.obexsocket.bind(("", 0))
            lightblue.advertise("OBEX Object Push", self.obexsocket, lightblue.OBEX)
            print "[OXR] Advertising OBEX Object Push on interface hci%d" % self.devid
            self.advertising = True
            self.cv.notify()
        self.cv.release()
        return self.devid

    def stopAdvertising(self):
        self.cv.acquire()
        try:
            lightblue.stopadvertise(self.obexsocket)
        except AttributeError:
            pass
        if self.devid: self.intrf.release(interface=self.devid, bandwidth=0)
        self.advertising = False
        self.cv.notify()
        self.cv.release()
        return self.devid


# --------------------------------------------
class ObexSend:
    def __init__(self, intrf):
        self.intrf = intrf
    
    def sendFile(self, address=None, channel=0, filepath="", maxretries = 3):
        status = 0
        retry = 0
        devid = self.intrf.request(bandwidth=1)
        while status <= 0 and retry <= maxretries:
            retry += 1
            print "[OXS] Sending file %s to device %s using channel %s and device %s (retry %s/%s)" % (str(filepath), str(address), str(channel), str(devid), str(retry), str(maxretries))
            try:
                lightblue.obex.sendfile(address, channel, filepath)
                #client = lightblue.obex.OBEXClient(device.address, device.getServiceChannel('OBEX Object Push'))
                #client.connect()
                #putresponse = client.put({"name": filepath}, file(filepath, 'rb'))
                #client.disconnect()
                status = 1
            except lightblue.obex.OBEXError:
                #raise lightblue.obex.OBEXError
                status = -1
                print "[OXS] error while sending file to device"
        self.intrf.release(interface=devid, bandwidth=1)
        return status
