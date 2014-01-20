import SimpleHTTPServer
import SocketServer
import socket
import json
import os
import string
from models import *
import semantify_local
import sqlite3, shlex, subprocess,  sys,  re,  time
from bs4 import BeautifulSoup as Soup
from bs4 import NavigableString
from datetime import datetime
import unicodedata
import numpy
import devutil
import codecs
import zlib

PORT = 50010

dbname='temp/livescore.db'


if not os.path.exists(dbname):
    # db should be initialized with: sqlite3 temp/semantify.db <schema.sql
    raise AssertionError('Database not found')    



conn = sqlite3.connect(dbname)
c = conn.cursor()
c.execute("PRAGMA foreign_keys = ON;")

# When changing database name, please do check  out the table name in the appropriate semantify_local_* file
path='/data/application/'


#   Opening error log 
errorlog=open(os.getcwd()+path+'errorlog.txt',  'w')
successlog=open(os.getcwd()+path+'successlog.txt',  'w')
filecount=0


class TestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
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
        f.write('<html><body>'.encode('utf-8'))
        for i in range(len(content)):                        
            f.write(content[i].encode('utf-8'))
        f.write('</body></html>'.encode('utf-8'))
        f.close()
        
        filename='file_'+now

        graph_id='first-order-chain'; performance_measure_id='accuracy'; single_pass=False; verbose=False
        
        test_file                        =os.getcwd()+path+'/temp/'+filename+'.test'
        test_reference_file         =os.getcwd()+path+'/temp/'+filename+'.test.reference'  
        
        train_file                       =os.getcwd()+path+'/temp/'+filename+'.train'   
        devel_file              =os.getcwd()+path+'/temp/'+filename+'.train.devel' 
        devel_prediction_file      =os.getcwd()+path+'/temp/'+filename+'.devel.prediction' 
        test_prediction_file         =os.getcwd()+path+'/temp/'+filename+'.test.prediction'
        model_file                 =os.getcwd()+path+'/temp/client.model'   
        
        page=open(os.getcwd()+path+filename+'.html')        
           
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
            words, f_ortho1,  f_ortho3, f_html, labels, sentences, nodes, node_index, tokens=semantify_local.preprocess_file(page)
            semantify_local.transactions(conn,  page_id, words, f_ortho1,  f_ortho3, f_html,   labels)
            value=semantify_local.history(conn, path, filename)         
            if value==1:
                print "initialize model"
                m = Model()
                print "done"
                print
                print "train model"
                accuracy=m.train(graph_id,  performance_measure_id,  single_pass,  train_file,  devel_file, devel_prediction_file,  verbose)
                print "done"    
                print
                print "save model"
                m.save(model_file)
                print "done"
                print                
                print accuracy                
                successlog.write(filename)
                successlog.write('\t')
                successlog.write( str(datetime.now()))
                successlog.write('\n') 
                elapsed=time.time()-t
                print 'File', filename, 'handled in:',  elapsed
                
                o['accuracy']=accuracy   
                self.wfile.write(json.dumps(o))            
                pass       
        
        elif o["command"] == "TAG":
            # Applies tags to the web page      
            value=0
            
            words, f_ortho1,  f_ortho3, f_html, labels, sentences, token_nodes, node_index, tokens=semantify_local.preprocess_file(page, build_node_index = True)
            semantify_local.write_testfiles(path, filename, sentences)                        
            
            print 'Devel files extracted' 
            print "load model"
            m=Model()
            m.load(model_file)
            print "done"
            print
            print "apply model"
            print (test_file, test_prediction_file, test_reference_file, verbose)
            m.apply(test_file, test_prediction_file, test_reference_file, verbose)
            print "done"
            print
            
            print "Reading in prediction file"
            print

            retfile=open(os.getcwd()+path+'/temp/'+filename+'.test.prediction')

            for node, tags in semantify_local.nodeblocks(retfile, tokens, lambda x: x not in ['O', 'START', 'STOP']):
                print (node, tags)
                devutil.keyboard()
                

            tagnodes, tagoffsets, tags = semantify_local.extract_tagged_nodes(retfile, tokens)

            devutil.keyboard()
            
            content=semantify_local.keywordtag(path, filename)                        
            successlog.write(filename)
            successlog.write('\t')
            successlog.write( str(datetime.now()))
            successlog.write('\n')             
            
            o['content']=''.join(content)                     
            
            self.wfile.write(json.dumps(o))
            elapsed=time.time()-t
            print 'File', filename, 'served in:',  elapsed                 
        
class MyTCPServer(SocketServer.TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)


httpd = MyTCPServer(("localhost", PORT), TestHandler)

if __name__ == "__main__":
    print "serving at port", PORT  
    httpd.serve_forever()
