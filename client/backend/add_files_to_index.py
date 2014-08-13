import sys
import backend
import devutil 

# Usage add_files_to_index.py model_name dtdfile file1 file2 ... filen

b = backend.Backend()

model_name = sys.argv[1]
dtdfile = sys.argv[2]

assert(dtdfile[-4:] == ".dtd")

for i in range(3, len(sys.argv)):
    try:
        page_id = b.insert_pages_annotated(model_name, dtdfile, sys.argv[i], False, open(sys.argv[i]))
        sys.stderr.write("Inserted %s as page %d\n" % (sys.argv[i], page_id))
    except Exception as e:
        sys.stderr.write("Adding file failed, %s\n" % str(e))

