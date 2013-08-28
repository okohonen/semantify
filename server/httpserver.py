import SimpleHTTPServer
import SocketServer
#import devutil
import json
import os
import string
import semantify
import sqlite3, shlex, subprocess,  sys,  re,  time
from bs4 import BeautifulSoup as Soup
from bs4 import NavigableString
from datetime import datetime

PORT = 50010

conn = sqlite3.connect('sample.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS samples (id INTEGER PRIMARY KEY AUTOINCREMENT, content text, added datetime)''')

#   Opening error log 
errorlog=open(os.getcwd()+'/temp/errorlog.txt',  'w')
successlog=open(os.getcwd()+'/temp/successlog.txt',  'w')

# Garbage collection in database
GC=1

class TestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """The test example handler."""

    def do_POST(self):
        """Handle a post request by returning the square of the number."""
        length = int(self.headers.getheader('content-length'))        
        data_string = self.rfile.read(length)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')        
        self.end_headers()
        t=time.time()

        o = json.loads(data_string) 
        # Writing to a file for processing
        f=open(os.getcwd()+"/temp/snippetfile.html", 'w')    
        content=o['content']
        f.write('<html><head><body>')
        for i in range(len(content)):            
            f.write(content[i].encode('utf8'))
        f.write('</body></head></html>')
        f.close()
        filename=   'snippetfile'
        
        if o["command"] == "PUT":            
            # Do what should be done during PUT
            
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
            pass
        elif o["command"] == "TAG":
            # Replace this line with real action
            
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
                     command='python apply.py --model_file %s --test_file %s --prediction_file %s' % (standardmodel,testfile, segmentationfile)
                     args = shlex.split(command)
                     process=subprocess.Popen(args)
                     process.wait()  
                     print 'Model Applied'
                     content=semantify.keywordtag(filename)                        
            successlog.write(filename)
            successlog.write('\t')
            successlog.write( str(datetime.now()))
            successlog.write('\n')             
            
            o['content']=''.join(content)
                
            
            self.wfile.write(json.dumps(o))
        elapsed=time.time()-t
        print 'File', filename, 'served in:',  elapsed
                           

httpd = SocketServer.TCPServer(("", PORT), TestHandler)

if __name__ == "__main__":
    print "serving at port", PORT
    httpd.serve_forever()
