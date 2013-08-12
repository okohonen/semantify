#!/usr/bin/env python

"""
A simple echo server
"""

import socket
import sqlite3
import json
import urllib2
import os
import re

print 'Starting server..\n\n'
host = 'localhost'
port = 50001
backlog = 5
size = 4096
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((host,port))
sock.listen(backlog)
print 'Server up and running...\n'
i=1

reg=re.compile('FileOver')
while True:
	
	client, address = sock.accept() 
	print 'Client connected'
	print 'Client address:' ,str(address),'\n'
	try:				
		data=client.recv(size)	
		while data:
			if not data=='Completed':					
				#print 'Receiving file:',i	   				
				f = open(os.getcwd()+"/file_"+str(i)+".html",'w') 		
   				i=i+1				
				if data:				
					while not data=='FileOver':						
						f.write(data)
						client.send('200')												
						data=client.recv(size)						
				
					print 'Received file id:',i-1
					f.close()
					client.send('404')					
					data=client.recv(size)					
					continue
										
			else:									
				print 'Receiving completed'
				break
			
		client.close()
		print 'Client:', address, 'disconnected'
	except Exception as e:
		raise e
		
	finally:
		client.close()			
				
	
sock.close()
		

