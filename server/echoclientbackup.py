#!/usr/bin/env python

"""
A simple echo client
"""

import socket
import sqlite3
import json, simplejson
import urllib2
import time



host = 'localhost'
port = 50007
size = 4096
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host,port))


# json  type argument passing

url=(['en.wikipedia.org','www.aalto.fi','into.aalto.fi'])
content=(["Wikipedia page","Aalto homepage","Aalto into page"])

failed = False
for i in range(len(url)):
  jsonstr= json.dumps({'url': url[i], 'content': content[i]})
  s.send('PUT\n\n%s' % jsonstr)  
  print 'PUT\n\n%s' % jsonstr

  data = s.recv(4096)
  print "Received"
  if data == "\n200\n":
    print "Ok, sending next"
  else:
    print "Failure, stopping"
    print data 
    failed = True   
    break  


if not(failed):
  s.send('GET\n\n') 
  data = s.recv(4096) 
  while (data !="\n200\n"):
   print data     
   data = s.recv(4096)  

# data = s.recv(size)
  s.close()


