#!/usr/bin/python
import basics
import scheduler

import threading
import sys
import time

class Bluebox:
    def __init__(self):
        pass
    
    def __del__(self):
        pass

    def main(self, args):
        # behaviours: (event[a], rule[b]) -> action[a,b]
        #   when an 'event' happens and a 'rule' is loaded, the 'action' is called
        behaviours = {
           'newscan': ['deliverfile','postsighting','startextension'],
           'obexin': ['acceptfile'],
           'newruleslist': ['scan','advertise']
        }

        prefixrules = [('intelligentrules', 'True')]
        
        # preactions: [('action',[argument1, argument2])]
        #   actions called before the rules file loaded
        preactions = [
           ('dontscan', []),
           ('dontadvertise', [])
        ]
        
        # postactions: [('action',[argument1, argument2])]
        #   actions called after the rules file loaded
        postactions = []

        sched = scheduler.Scheduler(behaviours=behaviours, rulesfile='defaultrules.yml', preactions=preactions, postactions=postactions, prefixrules=prefixrules)
        sched.start()

        try:
            while 1:
                time.sleep(1)
                #print "  bluebox is still alive ^^"
                #print "  rules:",sched.rules
                #print "  events:",shed.listEvents()
                #print "  devices:",sched.modules['scanner'].knownDevices.list()
                time.sleep(10)
            print "BlueBox terminated."
            sys.exit(0)
        except KeyboardInterrupt:
            print "KILL SIGNAL RECEIVED"            
            sched.kill()
            print "BlueBox terminated (forced)."
            exit(1)


if __name__ == '__main__':
    Bluebox().main(sys.argv)