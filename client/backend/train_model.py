import sys
import backend
from crfs import *

# Usage add_files_to_index.py model_name 

b = backend.Backend()

train_file = sys.argv[1]
devel_file = sys.argv[2]
devel_prediction_file = sys.argv[3]
model_file = sys.argv[4]

verbose = True

filename = "data/temp/train.log"

t = time.time()

print "initialize model"
m = CRF()
print "done"
print
print "train model"

#accuracy=m.train(graph_id,  performance_measure_id,  single_pass,  train_file,  devel_file, devel_prediction_file,  verbose)
m.train(train_file, devel_file, devel_prediction_file, verbose)
print "done"    
print
print "save model"
m.save(model_file)
print "done"
print                
#print accuracy                
elapsed=time.time()-t
print 'File', train_file, 'handled in:',  elapsed
