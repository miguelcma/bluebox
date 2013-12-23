import threading
import obexmodule as obex
import basics
import re

class ActionRunner(threading.Thread):
    def __init__(self, state, modules, action, eventargs=[], ruleargs={}):
        threading.Thread.__init__(self)
        self.cv = threading.Condition()
        self.kill_received = False
        self.state = state
        self.modules = modules
        self.action = action
        self.eventargs = eventargs # [arg1, arg2, ...]
        self.ruleargs = ruleargs # {argname1:arg1, argname2:arg2, ...}

    def run(self):
        #print "RUNNING ACTION",self.action
        if self.action=="deliverfile": self.deliverfile(eventargs=self.eventargs, ruleargs=self.ruleargs)
        if self.action=="postsighting": self.postsighting(eventargs=self.eventargs, ruleargs=self.ruleargs)
        if self.action=="startextension": self.startextension(eventargs=self.eventargs, ruleargs=self.ruleargs)
        if self.action=="acceptfile": self.acceptfile(eventargs=self.eventargs, ruleargs=self.ruleargs)
        if self.action=="scan": self.scan(eventargs=self.eventargs, ruleargs=self.ruleargs)
        if self.action=="dontscan": self.dontscan(eventargs=self.eventargs, ruleargs=self.ruleargs)
        if self.action=="advertise": self.advertise(eventargs=self.eventargs, ruleargs=self.ruleargs)
        if self.action=="dontadvertise": self.dontadvertise(eventargs=self.eventargs, ruleargs=self.ruleargs)
        #del self
    
    def deliverfile(self, eventargs, ruleargs):
        # examples of arguments:
        #   eventargs = Sighting()
        #   ruleargs = {'url':'http://img705.imageshack.us/img705/3679/lolface.gif',
        #               'mac':'aa:bb:cc:dd:ee:ff',
        #               'rememberfor':'3600',
        #               'retrytimes':'3'}
        # state variables:
        #   sentfiles = (address, url, sendtime)
        sighting = eventargs
        if ruleargs.has_key('rememberfor'): rememberfor = ruleargs['rememberfor']
        else: rememberfor = 3600
        if self.state.get('sentfiles') == None: self.state.set('sentfiles', {})
        for device in sighting.devices:
            if not ruleargs['mac'] or ruleargs['mac'] == 'ANY' or device.address == ruleargs['mac']:
                if self.state.get('sentfiles').has_key((device.address, ruleargs['url'])): timeOfLastSent = self.state.get('sentfiles')[(device.address, ruleargs['url'])]
                else: timeOfLastSent = 0
                if timeOfLastSent < basics.Clock().getTimestamp()-rememberfor:
                    path = self.modules['resources'].get(ruleargs['url'])
                    if device.getServiceChannel('OBEX Object Push'): channel = device.getServiceChannel('OBEX Object Push')
                    elif device.getServiceChannel('OBEX File Transfer'): channel = device.getServiceChannel('OBEX File Transfer')
                    elif device.getServiceChannel('Object Push'): channel = device.getServiceChannel('Object Push')
                    else: channel = 0
                    if device.address and channel and path:
                        if ruleargs.has_key('retrytimes'): retrytimes = ruleargs['retrytimes']
                        else: retrytimes = 3
                        status = self.modules['obexsend'].sendFile(address=device.address, channel=channel, filepath=path, retrytimes=retrytimes)
                        if status>0:
                            self.state.variables['sentfiles'][(device.address, ruleargs['url'])] = basics.Clock().getTimestamp()
                            self.state.stored = False
                            print "[ACT] file %s sent to device %s" % (path, device.address)
                        else: print "[ACT] sending error or device rejected the file"
                    else: print "[ACT] not possible to send file. service channel unkown"
                else: print "[ACT] device %s already have file %s. will not send again." % (device.address, ruleargs['url'])
    
    def postsighting(self, eventargs, ruleargs):
        # examples of arguments:
        #   eventargs = Sighting()
        #   ruleargs = {}
        sighting = eventargs
        print "[ACT] Sending sighting to %s" % (ruleargs['url'])
        #print "DEBUG SIGHTING:",sighting
        #print "DEBUG SIGHTING",sighting.serialize()
        if ruleargs.has_key('sendempty'): sendempty=ruleargs['sendempty']
        else: sendempty=True
        if sendempty or sighting.getNumDevices()>0:
            path = self.modules['resources'].putContent(ruleargs['url'], sighting.serialize())
    
    def startextension(self, eventargs, ruleargs):
        # examples of arguments:
        #   eventargs = Sighting()
        #   ruleargs = {'extname':'wiimote',
        #               'configurl':'',
        #               'devaddress':'00:11:22:33:44:55',
        #               'devname':'Mary in a boat',
        #               'devclass':'0x1023',
        #               'startup':true,
        #               ''}
        pass # UNSTABLE
    
    def acceptfile(self, eventargs, ruleargs):
        # examples of arguments:
        #   eventargs = ['/tmp/receveivedfilepath', '00:11:22:33:44:55']
        #   ruleargs = {'url'='http://www.server.com/uploadfile.php?mac=$1&filename=$0'}
        #   tags that may be used on the url specified on the user configured rules: $filename and $mac
        filepath = eventargs[0]
        filename = eventargs[0].split('/')[-1]
        mac = eventargs[1]
        url = ruleargs['url']
        if filename: url = re.sub("\$filename", filename, url)
        else: url = re.sub("\$filename", "unknown", url)
        if mac: url = re.sub("\$mac", mac, url)
        else: url = re.sub("\$mac", "000000000000", url)
        self.modules['resources'].putFile(url, filepath)

    def scan(self, eventargs, ruleargs={}):
        # examples of arguments:
        #   eventargs = []
        #   ruleargs = {'scaninterval':'30',
        #               'getnames':true,
        #               'namechache':'120',
        #               'getservices':true,
        #               'scantimeout':'8',
        #               'nametimeout':'8',
        #               'servicetimeout':'8'}
        if ruleargs.has_key('scaninterval'): scaninterval=ruleargs['scaninterval']
        else: scaninterval=30
        if ruleargs.has_key('getnames'): getnames=ruleargs['getnames']
        else: getnames=False
        if ruleargs.has_key('namechache'): namechache=ruleargs['namechache']
        else: namechache=False
        if ruleargs.has_key('getservices'): getservices=ruleargs['getservices']
        else: getservices=False
        if ruleargs.has_key('scantimeout'): scantimeout=ruleargs['scantimeout']
        else: scantimeout=False
        if ruleargs.has_key('nametimeout'): nametimeout=ruleargs['nametimeout']
        else: nametimeout=False
        if ruleargs.has_key('servicetimeout'): servicetimeout=ruleargs['servicetimeout']
        else: servicetimeout=False
        self.modules['scanner'].startScanning(getnames=getnames,
                                               getservices=getservices,
                                               scaninterval=scaninterval,
                                               namechache=namechache,
                                               scantimeout=scantimeout,
                                               nametimeout=nametimeout,
                                               servicetimeout=servicetimeout)
        #self.modules['scanner'].startScanning(getnames=True, getservices=True)
        
    def dontscan(self, eventargs, ruleargs):
        # examples of arguments:
        #   eventargs = []
        #   ruleargs = {}
        self.modules['scanner'].stopScanning()

    def advertise(self, eventargs, ruleargs):
        # examples of arguments:
        #   eventargs = []
        #   ruleargs = {}
        devid = str(0)
        print "[ACT] Starting advertising. Please wait..."
        basics.Exec().execlp('hciconfig',['hci'+devid,'piscan'])
        if ruleargs.has_key('name') and ruleargs['name']:
            devname = ruleargs['name']
        elif basics.Uci().get('basics','hciname'):
            devname = basics.Uci().get('basics','hciname')
        else:
            devname = 'Bluebox'
        basics.Exec().execlp('hciconfig',['hci'+devid,'name', devname])
        print "[ACT] Name of device hci%s set to %s" % (devid, devname)
        devid = str(self.modules['obexreceive'].startAdvertising())

    def dontadvertise(self, eventargs, ruleargs):
        # examples of arguments:
        #   eventargs = []
        #   ruleargs = {}
        self.modules['obexreceive'].stopAdvertising()
        basics.Exec().execlp('hciconfig',['hci0','noscan'])

    def intelligentrules(self, eventargs, ruleargs):
        # examples of arguments:
        #   eventargs = [rules, filepath]
        #   ruleargs = {}
        pass
