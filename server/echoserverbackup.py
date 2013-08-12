#!/usr/bin/env python

"""
A simple echo server
"""

import socket
import sqlite3
import json
import urllib2
import time


host = 'localhost'
port = 50007
backlog = 5
size = 4096
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host,port))
s.listen(backlog)
client, address = s.accept()

conn = sqlite3.connect('sample.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS samples
            (id INTEGER PRIMARY KEY AUTOINCREMENT, url text, content text, added datetime)''')
try:
  while 1:
      data = client.recv(size)
      if data:
	  command, jsonstr = data.split("\n\n")
	  print (command, jsonstr)	  
	  print command
	  if command=="PUT":
            o = json.loads(jsonstr) 		    
	    c.execute('''insert into samples (url, content, added) VALUES (?,?,?)''',(o["url"],o["content"], '2013-06-25'))
            conn.commit()
	  elif command=="GET":	
	    c.execute('select * from samples')
	    for row in c.fetchall(): 
	    #print(row)	    
	     jsondumps=json.dumps(row)   
	     client.send(jsondumps)
             client.send("\n")	
	  #print url,content		    
	      
          client.send("\n200\n")

      

# except Exception as e:
#	raise e

#c.execute('select * from samples')
#for row in c.fetchall(): 
# print(row)    	
#print 'Successful: Message 200', data

finally:
  client.close()
  s.close()
  conn.close()


