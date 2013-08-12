#!/usr/bin/env python


import socket
import sqlite3
import json, simplejson
import urllib2
import os
import string




host = 'localhost'
port = 50001
size = 4096
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((host,port))


exportpages=['livescorenone.html', 'manutd.html']

for i in range(len(exportpages)):	
		f=open (os.getcwd()+"/"+exportpages[i], 'r') 
		l=f.read().split('\n')		
		for line in range(len(l)):
			if line <len(l)-1:
				if l[line]:
					sock.send(l[line])
					data=sock.recv(size)
					if data=='200':
						continue
					elif data==404:
						print 'Failure while transporting file'
					
			else:				
				f.close()
				#print 'FileOver'
				sock.send('FileOver')
				data=sock.recv(size)
				if data==404:
					break	

sock.send('Completed')
print 'Successfully transported files'
	


sock.close()



