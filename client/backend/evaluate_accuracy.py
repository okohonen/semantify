import sys
import backend
from crfs import *

b = backend.Backend()

test_reference_file = sys.argv[1]
test_prediction_file = sys.argv[2]
tagset = eval(sys.argv[3])

precisions, recalls, fs = backend.evaluate_results(test_reference_file, test_prediction_file, tagset)

print "               class\t\tpreci.\trecall\tf-score"
print "               ========================================"
for i in range(len(tagset)):
    print "%20s\t\t%5.4f\t%5.4f\t%5.4f" % (tagset[i], precisions[i], recalls[i], fs[i])

