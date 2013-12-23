#import urllib, urllib2, httplib
import httplib
import urllib
import basics
import base64
import re
import time
import threading

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

class Resources(threading.Thread):
    dl = {}

    def __init__(self):
        threading.Thread.__init__(self)
        self.cv = threading.Condition()
        self.kill_received = False

    #def run(self):
    #    while not self.kill_received:
    #        time.sleep(10)
    #    print "[SCH] Resources thread ended"
    #    exit(1)

    #def kill(self):
    #    print "[RES] killing Resources thread..."
    #    if(self.isAlive):
    #        self.kill_received = True
    #        self.cv.acquire()
    #        self.cv.notify()
    #        self.cv.release()

    def get(self, url=""):
        if(self.dl.has_key(url)):
          print '[RES] file', url, "already in cache"
          return self.dl[url]
        else:
          #try:
          print "[RES] downloading", url
          (path,obj) = urllib.urlretrieve(url)
          self.cv.acquire()
          self.dl[url] = path
          self.cv.release()
          return path
          #except:
          #  return None

    def putContent(self, url="", content="", maxretries=3):
        #headers = {"Content-Type": "text/plain", "Accept": "text/plain"}
        clock = basics.Clock()
        addr = "000000000000"
        #if filename.rfind(".")>=0: fileextension = filename.split(".")[1]
        fileextension = "txt"
        p = re.compile('http://([^/]+)(.*)')
        host = p.sub(r'\1',url)
        path = p.sub(r'\2',url)
        headers = {'Content-type':'application/xml'}
        retry = 0
        connected = False
        while not connected and retry < maxretries:
            retry += 1
            print "[RES] Sending data to host %s and path %s (retry %d of %d)..." % (host,path,retry,maxretries)
            try:
                conn = httplib.HTTPConnection(host)
                conn.request("POST", path, str(content), headers)
                response = conn.getresponse()
                conn.close()
                connected = True
            except:
                conn.close()
                connected = False
        #print "DATA: %s" % str(content)      
        if connected and response.status==200: print "Data sent to %s :)" % host
        elif connected: print "[RES] Error sending data to %s (%d)" % (host, response.status)
        else: print "[RES] Error sending data to %s" % host

    def putFile(self, url="", filepath="", maxretries=3):
        #headers = {"Content-Type": "text/plain", "Accept": "text/plain"}
        clock = basics.Clock()
        addr = "000000000000"
        if filepath.rfind(".")>=0: fileextension = filepath.split(".")[1]
        else: fileextension = "txt"
        stream1 = "<?xml version=\"1.0\" encoding=\"utf-8\" ?><btObexReport><reportDate>%s</reportDate><btObexReportItemsList>   <btObexReportItem><bluetoothEntity><deviceAddress>%s</deviceAddress></bluetoothEntity><deviceName><text>Unknown</text></deviceName><files><fileObject><file>" % (clock.getIsoTime(), addr)
        stream2 = "</file><fileExtension>%s</fileExtension></fileObject></files></btObexReportItem></btObexReportItemsList></btObexReport>" % fileextension
        #print "DEBUG: "+stream1+"CONTENT-HERE"+stream2
        p = re.compile('http://([^/]+)(.*)')
        host = p.sub(r'\1',url)
        path = p.sub(r'\2',url)
        headers = {'Content-type':'application/xml'}
        retry = 0
        connected = False
        while not connected and retry < maxretries:
            retry += 1
            print "[RES] Sending file %s to host %s and path %s (retry %d of %d)..." % (filepath,host,path,retry,maxretries)
            try:
                f = open(filepath, "rb")
                conn = httplib.HTTPConnection(host)
                conn.request("POST", path, (stream1 + base64.b64encode(f.read()) + stream2), headers)
                response = conn.getresponse()
                conn.close()
                f.close()
                del conn
                connected = True
            except:
                print "[RES] Error sending content to server"
                connected = False
        #print "DATA: %s" % str(content)      
        if connected and response.status==200: print "[RES] Data sent to %s :)" % host
        elif connected: print "[RES] Error sending data to %s (%d)" % (host, response.status)
        else: print "[RES] Error sending data to %s" % host

#    def put2(self, host="", path="", file=""):
#        http = httplib2.Http()
#        file = open(filename)
#        http.request(uri = host+path, method = 'POST', body=file.read(), headers = {'Content-type':'binary/octet-stream'})
#        file.close()

#    def putFile2(self, host="", path="", file=""):
#        #headers = {"Content-Type": "text/plain", "Accept": "text/plain"}
#        headers = {'Content-type':'binary/octet-stream'}
#        f = open(file, "rb")
#        conn = httplib.HTTPConnection(host)
#        conn.request("POST", path, f.read(), headers)
#        f.close()
#        response = conn.getresponse()
#        dir(response)
#        conn.close()
#        if(response.status==200): print "[RES] File sent to server :)"
#        else: print "[RES] Error sending file to server (%d)" % response.status

#    def putBoundary(self, url="", path=""): # NOT WORKING
#        headers = {"Content-Type": "multipart/form-data; boundary=------XAXAX", "Accept": "text/plain"}
#        f = open(path, "rb")
#        data = "------DEBUG\n"
#        data += "Content-Disposition: form-data; name=\"upload\"; filename=\"ahah.txt\"\n"
#        data += "Content-Type: text/plain\n\n"
#        data += ""
#        data += f.read()
#        data += "------DEBUG--\n"
#        f.close()
#        #params = urllib.urlencode({'a':1, 'b':2})
#        conn = httplib.HTTPConnection("martinsalmeida.com:80")
#        conn.request("POST", "/upload.php", data, headers)
#        response = conn.getresponse()
#        print response.status, response.reason
#        data = response.read()
#        print data
#        conn.close()

    def startServer(self):
        try:
            server = HTTPServer(('', 8080), MyHandler)
            print '[RES] started httpserver...'
            server.serve_forever()
        except KeyboardInterrupt:
            print '[RES] ^C received, shutting down server'
            server.socket.close()

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print "i am GET"
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("ok")

    def do_POST(self):
        print "i am post"
        #print dir(self.rfile)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("ok")
        #self.wfile.close()
        #print dir(self.wfile)
