import sys
import backend
from crfs import *

if "-h" in sys.argv:
    sys.exit("Usage: extract_tagset.py labeled_file1 labeled_file2 ... labeled_filen")

tagset_ = set()
for fname in sys.argv[1:]:
    for l in backend.labels(fname):
        tagset_.add(l)
print sorted(list(tagset_))

