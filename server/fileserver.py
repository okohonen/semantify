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
import shlex, subprocess
import sys
import semantify
import time



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
    
    #   Opening error log 
    errorlog=open(os.getcwd()+'/temp/errorlog.txt',  'w')
    successlog=open(os.getcwd()+'/temp/successlog.txt',  'w')

    # Garbage collection in database
    GC=1

    while True:
        client, address = sock.accept()         
        print 'Client connected'
        print 'Client address:' ,str(address),'\n' 
        t=time.time()

        try:		            
                      
            data=client.recv(size)
            print data
                
            if data=='PUT': 
                #data=client.recv(size) 
                #filename=data
                snippetfile=open(os.getcwd()+"/temp/snippetfile.html",'w')    
                snippetfile.write('<html><head><body>')
                while data:
                    data=client.recv(size)                    
                    snippetfile.write(data)    
                snippetfile.write('</html></head></body>')
                print 'HTML page received'
                print 'Client:', address, 'disconnected'                 
                snippetfile.close()
                filename='snippetfile'
                
                # Handling file operations.......
                
                trainfile               =os.getcwd()+'/temp/'+filename+'.train'    
                traindevelfile       =os.getcwd()+'/temp/'+filename+'.train.devel'
                testfile                 =os.getcwd()+'/temp/'+filename+'.test'
                testdevelfile         =os.getcwd()+'/temp/'+filename+'.test.devel'
                segmentationfile =os.getcwd()+'/temp/'+filename+'.segmentation' 
                clientmodel         =os.getcwd()+'/temp/'+filename+'.model'
                standardmodel          =os.getcwd()+'/morphochal2010+eng.model'
                   
                value=semantify.preprocess(filename)
                if value==1:
                    print 'Preprocessing complete'
                    value=0
                    value=semantify.develparse(filename)
                    if value==1:    
                         print 'Devel files extracted' 
                         command='python train.py --train_file %s --devel_file %s --prediction_file %s --model_file %s' % (trainfile,traindevelfile, segmentationfile, clientmodel)
                         args = shlex.split(command)
                         process=subprocess.Popen(args)
                         process.wait() 
                         print 'Model trained'
                         command='python apply.py --model_file %s --test_file %s --prediction_file %s' % (clientmodel,testfile, segmentationfile)
                         args = shlex.split(command)
                         process=subprocess.Popen(args)
                         process.wait()  
                         print 'Model Applied'
                         value=semantify.keywordtag(filename)                        
                successlog.write(filename)
                successlog.write('\t')
                successlog.write( str(datetime.now()))
                successlog.write('\n') 
                elapsed=time.time()-t
                print 'File', filename, 'served in:',  elapsed
                
            if GC%5==0:
                    semantify.garbagecollection()
                    GC=GC+1
                
        except Exception as e:
            raise e
            errorlog.write(filename)
            errorlog.write('\t')
            errorlog.write(str(datetime.now()))
            errorlog.write('\t')
            errorlog.write(str(e))       
            errorlog.write('\n')
    
        finally:
            client.close()			
            

    conn.close()
    sock.close()


    

