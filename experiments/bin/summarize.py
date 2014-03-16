import sys
import backend
import devutil
import cPickle

tagset = eval(open(sys.argv[1]).read())
assert(type(tagset) is list)

cms = []
for f in sys.argv[2:]:
    cms.append(cPickle.load(open(f)))

# devutil.keyboard()

combined = reduce(lambda x, y: x + y, cms)
precisions, recalls, fs = backend.cm_to_prf(combined)

print "               class\t\tpreci.\trecall\tf-score"
print "               ========================================"
for i in range(len(tagset)):
    print "%20s\t\t%5.4f\t%5.4f\t%5.4f" % (tagset[i], precisions[i], recalls[i], fs[i])

