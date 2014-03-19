# For testing the client: A server that serves as a TAG response the page fed to it at startup as an argument

import SimpleHTTPServer
import SocketServer
import socket
import json
import os
import string
#from models import *
import sqlite3, shlex, subprocess,  sys,  re,  time
from bs4 import BeautifulSoup
from bs4 import NavigableString
from datetime import datetime
import unicodedata
import numpy
#import devutil
import codecs
import zlib
import devutil
PORT = 50010



# When changing database name, please do check  out the table name in the appropriate semantify_local_* file
path='/data/application/'


#   Opening error log 
errorlog=open(os.getcwd()+path+'errorlog.txt',  'w')
successlog=open(os.getcwd()+path+'successlog.txt',  'w')
filecount=0


class MockHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def set_responsestr(self, responsestr):
        self.responsestr = responsestr

    def do_POST(self):
        """Handle a post request by learning or returning a tagged page."""
        length = int(self.headers.getheader('content-length'))        
        data_string = self.rfile.read(length)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')        
        self.end_headers()
        t=time.time()        
        o = json.loads(data_string) 
   
        if o["command"] == "PUT": 
            pass
        
        elif o["command"] == "TAG":
            # Applies tags to the web page      
            
            o['content']=open(sys.argv[1]).read()

            self.wfile.write(json.dumps(o))
        
class SemantifyTCPServer(SocketServer.TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)



if __name__ == "__main__":
    httpd = SemantifyTCPServer(("localhost", PORT), MockHandler)
    print "serving file '%s' at port %d" % (sys.argv[1], PORT)
    httpd.serve_forever()

