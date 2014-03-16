import sys
import backend
from crfs import *
import devutil

test_reference_file = sys.argv[1]
test_prediction_file = sys.argv[2]
tagset = eval(open(sys.argv[3]).read())
assert(type(tagset) is list)

precisions, recalls, fs, extended_tagset, cm = backend.evaluate_results(test_reference_file, test_prediction_file, tagset)

print "               class\t\tpreci.\trecall\tf-score"
print "               ========================================"
for i in range(len(extended_tagset)):
    print "%20s\t\t%5.4f\t%5.4f\t%5.4f" % (extended_tagset[i], precisions[i], recalls[i], fs[i])

if len(sys.argv) > 4:
    import cPickle
    cPickle.dump(cm, open(sys.argv[4], 'wb'))
