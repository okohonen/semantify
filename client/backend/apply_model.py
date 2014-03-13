import sys
import backend
from crfs import *

# Usage add_files_to_index.py model_name 

b = backend.Backend()

model_file = sys.argv[1]
test_file = sys.argv[2]
test_reference_file = sys.argv[3]
test_prediction_file = sys.argv[4]

verbose = True

t = time.time()

m=CRF()
m.load(model_file)
print "done"
print
print "apply model"
print (test_file, test_prediction_file, test_reference_file, verbose)
#m.apply(test_file, test_prediction_file, test_reference_file, verbose)
m.apply(test_file, test_prediction_file, verbose)
print "done"
print

elapsed=time.time()-t
print 'File', test_file, 'handled in:',  elapsed
