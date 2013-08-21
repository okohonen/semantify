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
from datetime import datetime


if __name__ == "__main__": 
      
    print 'Starting server..\n\n'
    host = 'localhost'
    port = 50001
    backlog = 5
    size = 4096
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host,port))
    sock.listen(backlog)
    print 'Server up and running...\n'
    
    conn = sqlite3.connect('sample.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS samples (id INTEGER PRIMARY KEY AUTOINCREMENT, content text, added datetime)''')

    while True:
        client, address = sock.accept()         
        print 'Client connected'
        print 'Client address:' ,str(address),'\n'         
        

        try:		
            
            #filename=client.recv(size)              
            data=client.recv(size)         
            print data
            
            if data=='SEND':
                data=client.recv(size)	   				
                f = open(os.getcwd()+"/temp/"+filename+".html",'w') 		
                        
                if data:				
                    while not data=='FileOver':						
                        f.write(data)
                        client.send('200')												
                        data=client.recv(size)	
            
                    f.close()
                    client.send('404')					
                    data=client.recv(size)	
                    print 'Receiving completed'
                client.close()
                print 'Client:', address, 'disconnected'
                continue
    
            elif data=='RECV':
                print 'Sending file to client'
                f = open(os.getcwd()+"/temp/"+filename+".html",'r') 
                l=f.read().split('\n')
                for line in range(len(l)):
                    if line <len(l)-1:
                        if l[line]:						
                            client.send(l[line])
                            data=client.recv(size)	
                            if data=='200':
                                continue
                            elif data==404:
                                print 'Unexpected error while transporting file'
                    else:				
                        f.close()
                        print 'FileOver'
                        client.send('FileOver')
                        data=client.recv(size)
                        if data==404:
                            break
                client.send('Completed')
                print 'Sending completed'
                client.close()             
                print 'Client:', address, 'disconnected'                
                continue
                
            elif data=='PUSH':                
                print 'Receiving tokens'
                data=client.recv(size)
                while not data=='DoneSendingTokens':                     
                    c.execute('''insert into samples (content, added) VALUES (?,?)''',(data, datetime.now()))
                    conn.commit()
                    client.send('200')
                    data=client.recv(size)
                client.send('404')
                client.close()
                
                print 'Received tokens'
                print 'Client:', address, 'disconnected'     
                continue
                 
                
            elif 'PUT' in data:
                snippet=[]
                snippetfile=open(os.getcwd()+"/temp/snippetfile.html",'wb') 
                print data
                while data:
                    data=client.recv(size)                    
                    snippet.append(data)
                    print data
                for i in snippet:
                    #i=i.replace('"', '\'')
                    i=i.replace('\"', '"')
                    snippetfile.write(i)
                print 'HTML page received'
                print 'Client:', address, 'disconnected'     
                
                
        except Exception as e:
            raise e
    
        finally:
            client.close()			
            

    conn.close()
    sock.close()


    

