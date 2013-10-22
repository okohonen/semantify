import SimpleHTTPServer
import SocketServer
import json
import os
import string
import semantify_local
import sqlite3, shlex, subprocess,  sys,  re,  time
from bs4 import BeautifulSoup as Soup
from bs4 import NavigableString
from datetime import datetime
import unicodedata
import numpy

PORT = 50010

conn = sqlite3.connect('experiment.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS ortho1html(id INTEGER PRIMARY KEY AUTOINCREMENT, entity, long, brief, iscapital, isnumber, hasnumber, hassplchars,classname, classlong, classbrief, parentname, grandparentname, greatgrandparentname, ancestors, tagsetname, added)''')
c.execute('''CREATE TABLE IF NOT EXISTS ortho3 (id INTEGER PRIMARY KEY AUTOINCREMENT, entity, longcurrent, briefcurrent, previousterm, longprevious, briefprevious, nextterm, longnext, briefnext,iscapital, isnumber, hasnumber, hassplchars, tagsetname, added)''')
c.execute('''CREATE TABLE IF NOT EXISTS ortho3html (id INTEGER PRIMARY KEY AUTOINCREMENT, entity, longcurrent, briefcurrent, previousterm, lonprevious, briefprevious, nextterm, longnext, briefnext,iscapital, isnumber, hasnumber, hassplchars, classname, classlong, classbrief, parentname, grandparentname, greatgrandparentname, ancestors,tagsetname, added)''')


# When changing database name, please do check  out the table name in the appropriate semantify_local_* file
dbname='experiment.db'
path='/data/application/'
tagindex=20
tagset=['genre','item', 'price', 'stock', 'features']
tagdict=['WebAnnotator_genre', 'WebAnnotator_item', 'WebAnnotator_price', 'WebAnnotator_stock', 'WebAnnotator_features']

#   Opening error log 
errorlog=open(os.getcwd()+path+'errorlog.txt',  'w')
successlog=open(os.getcwd()+path+'successlog.txt',  'w')
filecount=0

class TestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """The test example handler.""" 

    def do_POST(self):        
        """Handle a post request by learning or returning a tagged page."""
        length = int(self.headers.getheader('content-length'))        
        data_string = self.rfile.read(length)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')        
        self.end_headers()
        t=time.time()        
        o = json.loads(data_string) 
      
        # Writing to a file for processing   
        now=str(datetime.now().strftime('%Y%m%d_%H%M%S'))
        f=open(os.getcwd()+path+'file_'+now+'.html', 'w')   
        content=o['content']
        f.write('<html><body>')
        for i in range(len(content)):            
            f.write(content[i].encode('utf8'))
        f.write('</body></html>')
        f.close()
        
        filename='file_'+now

            
        testfile                        =os.getcwd()+path+'/temp/'+filename+'.test'
        testreferencefile         =os.getcwd()+path+'/temp/'+filename+'.test.reference'
        
        trainfile                       =os.getcwd()+path+'/temp/'+filename+'.train'    
        traindevelfile              =os.getcwd()+path+'/temp/'+filename+'.train.devel' 
        develpredictionfile      =os.getcwd()+path+'/temp/'+filename+'.devel.prediction' 
        testpredictionfile         =os.getcwd()+path+'/temp/'+filename+'.test.prediction'
        clientmodel                 =os.getcwd()+path+'/temp/client.model'   
        
       
        
        if o["command"] == "PUT":            
            # Trains a model wit received annotations  
            value=0
            value=semantify_local.preprocess(dbname, path, filename, tagset, tagdict, tagindex)                
            if value==1:   
                 command='python train.py --graph first-order-chain --performance_measure accuracy --train_file %s --devel_file %s --devel_prediction_file %s --model_file %s' % (trainfile,traindevelfile, develpredictionfile, clientmodel)              
                 args = shlex.split(command)
                 process=subprocess.Popen(args)
                 process.wait()           
                 successlog.write(filename)
                 successlog.write('\t')
                 successlog.write( str(datetime.now()))
                 successlog.write('\n') 
                 elapsed=time.time()-t
                 print 'File', filename, 'served in:',  elapsed
                 pass       
        
        elif o["command"] == "TAG":
            # Applies tags to the web page      
            value=0
            value=semantify_local.preprocess(dbname, path, filename, tagset, tagdict,  tagindex)            
            if value==1:    
                 print 'Devel files extracted' 
                 command='python apply.py --model_file %s --test_file %s --test_prediction_file %s' % (clientmodel,testfile, testpredictionfile)
                 args = shlex.split(command)
                 process=subprocess.Popen(args)
                 process.wait()  
                 content=semantify_local.keywordtag(path, filename, tagset, tagdict,  tagindex)                        
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
