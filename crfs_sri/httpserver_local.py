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
import devutil
import zlib

PORT = 50010
dbname='temp/semantify.db'

if not os.path.exists(dbname):
    # db should be initialized with: sqlite3 temp/semantify.db <schema.sql
    raise AssertionError('Database not found')
tagset=['entity',  'sentence', 'date']
tagdict=['WebAnnotator_entity', 'WebAnnotator_sentence', 'WebAnnotator_date']

conn = sqlite3.connect(dbname)
c = conn.cursor()
c.execute("PRAGMA foreign_keys = ON;")

# When changing database name, please do check  out the table name in the appropriate semantify_local_* file
path='/data/application/'
tagindex=20

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
            
            # TODO client sends schema identifier
            schema_id = 1;

            # Add to database
            # We have three cases:
            # 1. We are editing the latest version
            # 2. We are editing an older version
            # 3. We want to create a new version to edit
        
            # Case 3.
            if o.has_key("create_new"):
                c.execute('''SELECT MAX(version) FROM pages WHERE url=? AND schema_id=?''', (o['url'], schema_id))
                if c.rowcount > 0:
                    r = c.fetchone()
                    version = r[0] + 1;
                else:
                    version = 1;
                semantify_local.insert_new_page(c, o, version);
        
            # Case 2.
            if o.has_key("version"):
                c.execute('''SELECT id FROM pages WHERE url=? AND version=? AND schema_id=? ORDER BY timestamp DESC''', (o['url'], o['version'], schema_id))
                r = c.fetchone()
                if r is None:
                    # This is an error, since we should never insert an old version
                    raise ValueError("Cannot use version that does not exist")
                else:
                    page_id = r[0];
                    semantify_local.update_page(c, page_id, o)
                
            # Case 1.
            else:
                c.execute("SELECT id FROM pages WHERE url=? AND schema_id=? ORDER BY version DESC", (o['url'], schema_id))
                r = c.fetchone()                
                if r is None:
                    # Here we are doing the first insertion
                    page_id = semantify_local.insert_new_page(c, o, 1)
                else:
                    page_id = r[0];
                    semantify_local.update_page(c, page_id, o)
            conn.commit()       
        

            # Trains a model with received annotations  
            value=0
            tokens,  f_ortho1, f_ortho3,  f_html,   tags=semantify_local.preprocess(conn, path, filename, tagindex, page_id) 
            semantify_local.transactions(conn, path, page_id, tokens,  f_ortho1, f_ortho3,  f_html,   tags)
            value=semantify_local.history(conn, path, filename)            
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
                 print 'File', filename, 'handled in:',  elapsed
                 pass       
        
        elif o["command"] == "TAG":
            # Applies tags to the web page      
            value=0
            page_id=1            
            semantify_local.preprocess(conn, path, filename, tagindex, page_id)
            print 'Devel files extracted' 
            command='python apply.py --model_file %s --test_file %s --test_prediction_file %s' % (clientmodel,testfile, testpredictionfile)
            args = shlex.split(command)
            process=subprocess.Popen(args)
            process.wait()  
            content=semantify_local.keywordtag(path, filename, tagdict,  tagset,  tagindex)                        
            successlog.write(filename)
            successlog.write('\t')
            successlog.write( str(datetime.now()))
            successlog.write('\n')             
            
            o['content']=''.join(content)                     
            
            self.wfile.write(json.dumps(o))
            elapsed=time.time()-t
            print 'File', filename, 'served in:',  elapsed                 
        
               

httpd = SocketServer.TCPServer(("localhost", PORT), TestHandler)

if __name__ == "__main__":
    print "serving at port", PORT
    httpd.serve_forever()
