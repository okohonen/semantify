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

PORT = 50010

b = backend.Backend()


# When changing database name, please do check  out the table name in the appropriate semantify_local_* file
path='/data/application/'


#   Opening error log 
errorlog=open(os.getcwd()+path+'errorlog.txt',  'w')
successlog=open(os.getcwd()+path+'successlog.txt',  'w')
filecount=0

feature_set = "ortho3+html3"

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
        
        filename='file_'+now

        graph_id='first-order-chain'; performance_measure_id='accuracy'; single_pass=False; verbose=False
        
        test_file                        =os.getcwd()+path+'/temp/'+filename+'.test.gz'
        test_reference_file         =os.getcwd()+path+'/temp/'+filename+'.test.reference'  
        
        train_file                       =os.getcwd()+path+'/temp/'+filename+'.train'   
        devel_file              =os.getcwd()+path+'/temp/'+filename+'.train.devel' 
        devel_prediction_file      =os.getcwd()+path+'/temp/'+filename+'.devel.prediction' 
        test_prediction_file         =os.getcwd()+path+'/temp/'+filename+'.test.prediction'
        model_file                 =os.getcwd()+path+'/temp/client.model'   
        
        
        page = BeautifulSoup('<html><body>%s</body></html>' % o['content'], from_encoding = "utf-8")
   
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
                b.insert_pages_annotated(o['model_name'], o['dtd'], o['url'], True, o['content'])
        
            # Case 2.
            if o.has_key("version"):
                b.update_pages_annotated(o['model_name'], o['dtd'], o['url'], o['version'], True, o['content'])

            # Case 1.
            else:
                # If page already exists then update latest version
                b.insert_or_update_pages_annotated(o['model_name'], o['dtd'], o['url'], True, ['content'])
                # b.insert_or_update_pages_annotated(o['model_name'], o['dtd'], o['url'], o['content'].encode('utf-8'), True)

            # Incremental training with modulo criterion for train-devel split
            if not(its.has_key(o['model_name'])):
                its[o['model_name']] = it.TrainingFileBuilderIncrementalTraining(b.get_tmpdir(), o['model_name'], it.ModuloTrainDevelSplitter(10), resuming=True)
            
            its[o['model_name']].incremental_train(parsed_page.read_features(), devel_prediction_file, model_file)
        
        elif o["command"] == "TAG":
            # Applies tags to the web page      
            parsed_page = hp.parse_page(page, feature_set, annotated=False, build_node_index=True)
            
            parsed_page.write_feature_file(test_file)

            print 'Devel files extracted' 
            print "load model"
            m=CRF()
            m.load(model_file)
            print "done"
            print
            print "apply model"
            print (test_file, test_prediction_file, verbose)
            #m.apply(test_file, test_prediction_file, test_reference_file, verbose)

            m.apply(test_file, test_prediction_file, verbose)
            print "done"
            print
            
            print "Reading in prediction file"
            print

            retfile=open(os.getcwd()+path+'/temp/'+filename+'.test.prediction')

            parsed_page.apply_tagging(retfile)

            # nodes_to_tag = backend.extract_tagged_nodes(retfile, tokens)
            # print "Nodes to tag: %d" % len(nodes_to_tag)
            # print nodes_to_tag
            # backend.apply_tagging(page, nodes_to_tag, node_index)
            
            successlog.write(filename)
            successlog.write('\t')
            successlog.write(str(datetime.now()))
            successlog.write('\n')             
            
            s = str(parsed_page)
            o['content'] = str(parsed_page.get_body())

            self.wfile.write(json.dumps(o))

            elapsed=time.time()-t
            print 'File', filename, 'served in:',  elapsed                 
        
class SemantifyTCPServer(SocketServer.TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)


httpd = SemantifyTCPServer(("localhost", PORT), SemantifyHandler)

if __name__ == "__main__":
    print "serving at port", PORT  
    httpd.serve_forever()
