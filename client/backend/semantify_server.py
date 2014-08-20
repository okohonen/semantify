import SimpleHTTPServer
import SocketServer
import socket
import json
import os
import string
import backend
from crfs import *
import sqlite3, shlex, subprocess,  sys,  re,  time
from bs4 import BeautifulSoup
from bs4 import NavigableString
from datetime import datetime
import unicodedata
import numpy
import devutil
import codecs
import zlib
import incremental_training as it
import feature_file as ff
import htmlparse as hp
import threading

PORT = 50010

b = backend.Backend()


# When changing database name, please do check  out the table name in the appropriate semantify_local_* file
path='/data/temp/'


#   Opening error log 
errorlog=open(os.getcwd()+path+'errorlog.txt',  'w')
successlog=open(os.getcwd()+path+'successlog.txt',  'w')
filecount=0

feature_set = "ortho3+html1"

its = {}

class SemantifyHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_POST(self):
        """Handle a post request by learning or returning a tagged page."""
        length = int(self.headers.getheader('content-length'))        
        data_string = self.rfile.read(length)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')        
        self.end_headers()
        t=time.time()        
        o = json.loads(data_string) 
      
        print o["command"]

        # Writing to a file for processing   
        now=str(datetime.now().strftime('%Y%m%d_%H%M%S'))
        # No need for html-file, we already have it in memory
        # f=open(os.getcwd()+path+'file_'+now+'.html', 'w')   
        # content=o['content']
        # f.write('<html><body>'.encode('utf-8'))
        # for i in range(len(content)):                        
        #     f.write(content[i].encode('utf-8'))
        # f.write('</body></html>'.encode('utf-8'))
        # f.close()                
        
        if o.has_key("content"):
            page = BeautifulSoup('<html><body>%s</body></html>' % o['content'], from_encoding = "utf-8")
            
            # Save to file for debugging
            outfp = open("out.html", 'w')
            outfp.write('<html><body>%s</body></html>' % o['content'].encode("utf8"))
            outfp.close()
   
        if o["command"] == "PUT": 

            parsed_page = hp.parse_page(page, feature_set, annotated=True, build_node_index=False)
            # TODO client sends schema identifier
            schema_id = 1;

            # Add to database
            # We have three cases:
            # 1. We are editing the latest version
            # 2. We are editing an older version
            # 3. We want to create a new version to edit
        
            # Case 3.
            if o.has_key("create_new"):                
                page_id = b.insert_pages_annotated(o['model_name'], o['dtd'], o['url'], True, o['content'])
        
            # Case 2.
            if o.has_key("version"):
                page_id = b.update_pages_annotated(o['model_name'], o['dtd'], o['url'], o['version'], True, o['content'])

            # Case 1.
            else:
                # If page already exists then update latest version
                page_id = b.insert_or_update_pages_annotated(o['model_name'], o['dtd'], o['url'], True, o['content'])
                # b.insert_or_update_pages_annotated(o['model_name'], o['dtd'], o['url'], o['content'].encode('utf-8'), True)

            # Incremental training with modulo criterion for train-devel split
            if not(its.has_key(o['model_name'])):
                its[o['model_name']] = it.TrainingFileBuilderIncrementalTraining(b.get_tmpdir(), o['model_name'], feature_set, it.ModuloTrainDevelSplitter(10), b)
            
            its[o['model_name']].incremental_train(parsed_page.read_features(), page_id)
        
        elif o["command"] == "TAG":
            print (o["url"], o["model_name"])
            # Applies tags to the web page      
            parsed_page = hp.parse_page(page, feature_set, annotated=False, build_node_index=True)
            model = b.get_tagger(o['model_name'], feature_set)
            parsed_page.apply_tagging(model.tag(parsed_page))
            
            successlog.write('\t')
            successlog.write(str(datetime.now()))
            successlog.write('\n')             
            
            o['content'] = str(parsed_page.get_body())

            self.wfile.write(json.dumps(o))

            elapsed=time.time()-t
            print 'File served in:',  elapsed                 
    
        elif o["command"] == "GETMODELS":
            models = b.get_models()
            ret = []
            for m in models:
                ret.append({"name": m["name"], "dtd": m["dtdfile"], "lastused": 0})
            self.wfile.write(json.dumps(ret))

            
        
class SemantifyTCPServer(SocketServer.TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)


httpd = SemantifyTCPServer(("localhost", PORT), SemantifyHandler)

if __name__ == "__main__":
    print "serving at port", PORT  
    httpd.serve_forever()
    
