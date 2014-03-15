import sys
import backend
from crfs import *



b = backend.Backend()

if "-h" in sys.argv or len(sys.argv) != 4:
    sys.exit("Usage: search_indexed_files.py model_name sort_order\n")

model_name = sys.argv[1]
sort_order = sys.argv[2]
feature_set = sys.argv[3]

print b.extract_dataset_files(model_name, feature_set, order_by=sort_order)
