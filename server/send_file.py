
import socket
import sqlite3
import json, simplejson
import urllib2
import os
import string

if __name__ == "__main__":
    
    def send_file(self, filename):
        host = 'localhost'
        port = 50001
        size = 4096
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host,port))
        size=4096   
        
        sock.send(filename)
        f=open(os.getcwd()+"/"+filename+".html", 'w')
        sock.send('RECV')

        data=sock.recv(size)
        if data:
    
            while not data=='FileOver':						
                f.write(data)
                sock.send('200')												
                data=sock.recv(size)	
    
            f.close()
            sock.send('404')					
            data=sock.recv(size)
            print data
            if data=='Completed':	
                sock.close()
        #print 'Receving completed'					
    
        return 1



