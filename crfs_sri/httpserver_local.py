import SimpleHTTPServer
import SocketServer
#import devutil
import json
import os
import string
import semantify_local
import sqlite3, shlex, subprocess,  sys,  re,  time
from bs4 import BeautifulSoup as Soup
from bs4 import NavigableString
from datetime import datetime

PORT = 50010

conn = sqlite3.connect('sentence.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS sentences (id INTEGER PRIMARY KEY AUTOINCREMENT, entity text, tag text, added datetime)''')

#   Opening error log 
errorlog=open(os.getcwd()+'/temp/errorlog.txt',  'w')
successlog=open(os.getcwd()+'/temp/successlog.txt',  'w')

# Garbage collection in database
#GC=1

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
        counter=0
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
            testreferencefile         =os.getcwd()+'/temp/'+filename+'.test.reference'
            develpredictionfile =os.getcwd()+'/temp/'+filename+'.devel.prediction' 
            testpredictionfile         =os.getcwd()+'/temp/'+filename+'.test.prediction'
            clientmodel         =os.getcwd()+'/temp/'+filename+'.model'
            standardmodel          =os.getcwd()+'/morphochal2010+eng.model'
               
            value=semantify_local.preprocess(filename)
            if value==1:
                print 'Preprocessing complete'
                value=0
                value=semantify_local.develparse(filename)
                if value==1:    
                     print 'Devel files extracted' 
                     command='python train.py --graph first-order-chain --performance_measure accuracy --train_file %s --devel_file %s --devel_prediction_file %s --model_file %s --verbose' % (trainfile,traindevelfile, develpredictionfile, clientmodel)
                     print command
                     args = shlex.split(command)
                     process=subprocess.Popen(args)
                     process.wait() 
                     print 'Model trained'
                     command='python apply.py --model_file %s --test_file %s --test_prediction_file %s --verbose' % (clientmodel,testfile, testpredictionfile)
                     print command
                     args = shlex.split(command)
                     process=subprocess.Popen(args)
                     process.wait()  
                     print 'Model Applied'
                     content=semantify_local.keywordtag(filename)                       
            successlog.write(filename)
            successlog.write('\t')
            successlog.write( str(datetime.now()))
            successlog.write('\n') 
            elapsed=time.time()-t
            print 'File', filename, 'served in:',  elapsed
            
            #if GC%5==0:
                    #semantify_local.garbagecollection()
                    #GC=GC+1
            pass
            
        elif o["command"] == "TAG":
            # Replace this line with real action
            
            trainfile               =os.getcwd()+'/temp/'+filename+'.train'    
            traindevelfile       =os.getcwd()+'/temp/'+filename+'.train.devel'
            develpredictionfile= os.getcwd()+'/temp/'+filename+'.devel.prediction' 
            testfile                 =os.getcwd()+'/temp/'+filename+'.test'
            testdevelfile         =os.getcwd()+'/temp/'+filename+'.test.devel'
            testpredictionfile =os.getcwd()+'/temp/'+filename+'.test.prediction' 
            testreferencefile = os.getcwd()+'/temp/'+filename+'.test.reference' 
            clientmodel         =os.getcwd()+'/temp/'+filename+'.model'
            standardmodel          =os.getcwd()+'/models/wsj.first-order-chain.model'
               
            value=semantify_local.preprocess(filename)
            if value==1:
                print 'Preprocessing complete'
                value=0
                value=semantify_local.develparse(filename)
                if value==1:    
                     print 'Devel files extracted' 
                     command='python train.py --graph first-order-chain --performance_measure accuracy --train_file %s --devel_file %s --devel_prediction_file %s --model_file %s --verbose' % (trainfile,traindevelfile, develpredictionfile, clientmodel)
                     args = shlex.split(command)
                     process=subprocess.Popen(args)
                     process.wait() 
                     print 'Model trained'
                     command='python apply.py --model_file %s --test_file %s --test_prediction_file %s --test_reference_file %s --verbose' % (clientmodel,testfile, testpredictionfile, testreferencefile)
                     args = shlex.split(command)
                     process=subprocess.Popen(args)
                     process.wait()  
                     print 'Model Applied'
                     content=semantify_local.keywordtag(filename)                        
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
