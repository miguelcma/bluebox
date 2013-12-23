import datetime
import time
import re
import subprocess
from subprocess import PIPE
from subprocess import STDOUT

class Uci:
    def __init__(self):
        pass

    def get(self, section, option):
        proc = subprocess.Popen(["uci", "get", "bluebox.%s.%s" % (section, option)], stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
        proc.wait()
        if proc.returncode:
            ret = None
        else:
            ret = re.sub("\n$","", proc.stdout.read())
        return ret

class Exec:
    def __init__(self):
        pass
    
    def execlp(self, bin, args=[], wait=True):
        proc = subprocess.Popen(([bin]+args), stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
        #print "Executing",[bin]+args
        if wait:
            proc.wait()
            if proc.returncode:
                ret = None
            else:
                ret = proc.stdout.read()
            return ret
        else:
            return None


class Clock:
    def getIsoTime(self):
        return datetime.datetime.isoformat(datetime.datetime.now().replace(microsecond=0))
    def getTimestamp(self):
        return int(time.time())
    def getMicroTimestamp(self):
        return time.time()

# -------------------------------------------------
class Log:
    def __init__(self):
        pass


