#!/usr/bin/env python


import socket
import sqlite3
import json, simplejson
import urllib2
import os
import string

#if __name__ == "__main__":
def receive_file(filename):
    host = 'localhost'
    port = 50001
    size = 4096
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host,port))    

    sock.send(filename)	
    f=open (os.getcwd()+"/"+filename+".html", 'r') 
    sock.send('SEND')
    l=f.read().split('\n')		
    for line in range(len(l)):
        if line <len(l)-1:
            if l[line]:
                sock.send(l[line])
                data=sock.recv(size)
                if data=='200':
                    continue
                elif data==404:
                    print 'Unexpected error while transporting file'					
        else:				
            f.close()		
            sock.send('FileOver')
            data=sock.recv(size)
            if data==404:
                break	

    sock.send('Completed')
    #print 'Sending completed'
    sock.close()
    return 1



