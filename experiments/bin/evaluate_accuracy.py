import sys
import backend
from crfs import *

b = backend.Backend()

test_reference_file = sys.argv[1]
test_prediction_file = sys.argv[2]

precisions, recalls, fs, tagset = backend.evaluate_results(test_reference_file, test_prediction_file)

print "               class\t\tpreci.\trecall\tf-score"
print "               ========================================"
for i in range(len(tagset)):
    print "%20s\t\t%5.4f\t%5.4f\t%5.4f" % (tagset[i], precisions[i], recalls[i], fs[i])

