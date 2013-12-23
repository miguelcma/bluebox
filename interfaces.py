import threading
import bluetooth
import time

class Interfaces(threading.Thread):
    interfaces = {} # index: 0=hci0, 1=hci1, ...
                    # value: {'inusebandwidth':...,'lock':...}
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.cv = threading.Condition()
        self.kill_received = False
        self.interfaces = {}
        self._findInterfaces()

    def run(self):
        while not self.kill_received:
            self.cv.acquire()
            self.cv.wait()
            self.cv.release()
            #time.sleep(10)
            print "[INT] searching for new interfaces"
        
        print "[INT] Interfaces thread ended"
        exit(1)

    def kill(self):
        if(self.isAlive):
            self.kill_received = True
            self.cv.acquire()
            self.cv.notify()
            self.cv.release()

    def _findInterfaces(self):
        count = 0
        i = bluetooth._bluetooth.hci_devid()
        devid = bluetooth._bluetooth.hci_devid("hci%d"%i)
        while devid > -1:
            count += 1
            self.interfaces[devid] = {}
            self.interfaces[devid]['inusebandwidth'] = 0
            #self.interfaces[interface]['lock'] = threading.Condition()
            i += 1
            devid = bluetooth._bluetooth.hci_devid("hci%d"%i)
        print "[INT] found %d interfaces" % count

    def request(self, bandwidth=1):
        chosen = -2 # -2 means not chosen
                    # -1 means auto chosing
                    #  0 means hci0
                    #  1 means hci1
                    #  ...
        #chosen = 0 # TEMPORARIO
        while chosen == -2:
            for interface in self.interfaces:
                if chosen == -2 and bandwidth <= 8-self.interfaces[interface]['inusebandwidth']:
                    chosen = interface
            if chosen == -2:
                self.cv.acquire()
                self.cv.wait()
                self.cv.release()
        #self.interfaces[chosen]['lock'].acquire()
        # self.interfaces[chosen]['bandwidth'] += bandwidth
        self.interfaces[chosen]['inusebandwidth'] += bandwidth
        print "[INT] requested", "%s/8"%bandwidth, "slots from interface", "hci%s"%interface
        return chosen
    
    def release(self, interface, bandwidth=1):
        self.interfaces[interface]['inusebandwidth'] -= bandwidth
        if self.interfaces[interface]['inusebandwidth']<0: self.interfaces[interface]['inusebandwidth'] = 0
        #self.interfaces[interface]['lock'].release()
        self.cv.acquire()
        self.cv.notifyAll()
        self.cv.release()
        print "[INT] realeased", bandwidth, "slots from interface", "hci%s"%interface

    def getNumInterfaces(self):
        return interfaces.__len__()
