import obexmodule as obex
import scanner
import resources
import devices
import actions
import interfaces

import threading
import yaml
import time
import pickle

class StateManager(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.cv = threading.Condition()
        self.kill_received = False
        self.variables = {}
        self.stored = True
        self.load('state.pkl')

    def run(self):
        while not self.kill_received:
            self.cv.acquire()
            self.cv.wait()
            self.cv.release()
            #time.sleep(5)
            if not self.stored: self.store('state.pkl')
            else: print "[SCH] state already stored. Nothing done."
        #print "[SCH] StateManager thread ended"

    def kill(self):
        if(self.isAlive):
            self.kill_received = True
            self.cv.acquire()
            self.cv.notify()
            self.cv.release()

    def set(self, var, value):
        self.cv.acquire()
        self.variables[var] = value
        self.stored = False
        self.cv.release()
        print "[SCH] State changed. Not stored yet"

    def get(self, var):
        if not self.variables.has_key(var): return None
        return self.variables[var]

    def list(self):
        return self.variables[var]

    def acquireLock(self):
        self.cv.acquire()

    def releaseLock(self):
        self.cv.release()

    def store(self, filepath='state.pkl'):
        try:
            output = open(filepath, 'wb')
            pickle.dump(self.variables, output)
            output.close()
            self.cv.acquire()
            self.stored = True
            self.cv.release()
            print "[SCH] State stored in %s" % filepath
        except IOError:
            print "[SCH] Could not write to file %s. No state was loaded." % filepath

    def load(self, filepath='state.pkl'):
        try:
            self.cv.acquire()
            pkl_file = open(filepath, 'rb')
            self.variables = pickle.load(pkl_file)
            pkl_file.close()
            self.cv.release()
            print "[SCH] State loaded from %s" % filepath
        except (IOError, EOFError):
            self.cv.release()
            print "[SCH] File %s doesn't exist. No state was loaded." % filepath
        

class Scheduler(threading.Thread):
    events = [] # (eventname,args[])
    loadedActions = []
    modules = {}
    
    # (event[a], rule[b]) -> action[a,b]
    #behaviours = {
    #  'newscan': ['deliverfile','postsighing','startextension'],
    #  'obexin': ['acceptfile'],
    #  'newruleslist': ['startScanning','startAdvertising']
    #}

    # [('rule1',{'arg1':'value1', 'arg2':'value2'})]
    #rules = [
    #    ('deliverfile',{'url':'http://www.google.com/logo.png','mac':'00:17:E4:EA:45:51'}),
    #    ('sendscanning',{'url':'http://www.google.com/postsightings.php'})
    #]
    
    def __init__(self, behaviours={}, rulesfile="", preactions=[], postactions=[], prefixrules=[]):
        threading.Thread.__init__(self)
        self.cv = threading.Condition()
        self.kill_received = False
        self.behaviours = behaviours
        self.preactions = preactions
        self.postactions = postactions
        self.prefixrules = prefixrules
        self.defaultrulesfile = rulesfile

        # MANAGERS and MODULES:
        self.state = StateManager()
        self.modules['interface'] = interfaces.Interfaces()
        self.modules['scanner'] = scanner.Scanner(self, self.modules['interface'])
        self.modules['obexreceive'] = obex.ObexReceive(self, self.modules['interface'])
        self.modules['obexsend'] = obex.ObexSend(self.modules['interface'])
        self.modules['resources'] = resources.Resources()
        #self.modules['extensions'] = extensions.Extensions()
        #
        self.state.start()
        self.modules['scanner'].start()
        self.modules['obexreceive'].start()
        #self.modules['resources'].start()

    def run(self):
        if self.defaultrulesfile:
                self.loadRulesFromFile(self.defaultrulesfile)
        print "[SCH] Scheduler thread running"
        while not self.kill_received:
            self.cv.acquire()
            self.cv.wait()
            self.cv.release()
        self.state.kill()
        self.modules['scanner'].kill()
        self.modules['obexreceive'].kill()
        print "[SCH] Scheduler thread ended"
        #exit(1)
    
    def kill(self):
        #print "[SCH] killing Scheduler thread..."
        if(self.isAlive):
            self.kill_received = True
            self.cv.acquire()
            self.cv.notify()
            self.cv.release()

    #def setModules(self, modules):
    #    self.modules = modules

    def loadRulesFromFile(self, filepath=""):
        for preaction in self.preactions:
            self._runAction(preaction[0], 'preaction', preaction[1], {})
        rules = yaml.load(file(filepath,'r').read())
        rules2 = []
        rules2.extend(self.prefixrules)
        count = 0
        if rules:
            for rule in rules:
                for rulename in rule:
                    if rule[rulename] == None: rule[rulename] = {}
                    rules2.append((rulename,rule[rulename]))
                count += 1
        self.cv.acquire()
        self.rules = rules2
        self.cv.release()
        for postaction in self.postactions:
            self._runAction(postaction[0], 'postaction', postaction[1], {})
        self.pushEvent('newruleslist',[rules, filepath])
        print "[SCH] loaded %d rules from %s" % (count, filepath)

    def _runAction(self, action, event, eventargs, ruleargs):
        #print "[SCH] calling action %s by the event %s(%s) using the rule %s(%s)\n" % (action, event, eventargs, action, ruleargs)
        action = actions.ActionRunner(state=self.state, modules=self.modules, action=action, eventargs=eventargs, ruleargs=ruleargs)
        action.start()
        self.loadedActions.append(action)

    def pushEvent(self, name = "", args = []):
        #self.cv.acquire()
        #self.events.insert(0,(name, args))
        for b in self.behaviours[name]:
            for r in self.rules:
                if b==r[0]:
                    self._runAction(b,name,args,r[1])
        #self.cv.notify()
        #self.cv.release()
    
    #def popEvent(self, name):
    #    self.cv.acquire()
    #    for i in self.events:
    #        if(name == i[0]):
    #            self.events.remove((name,i[1]))
    #            return i[1]
    #    self.cv.notify()
    #    self.cv.release()
    #    return None
    
    #def listEvents(self):
    #    return self.events

    #def countEvents(self):
    #    return self.events.__len__()
