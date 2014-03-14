import sys
import backend

# Usage add_files_to_index.py model_name file1 file2 ... filen

b = backend.Backend()

model_name = sys.argv[1]

if not(model_name in b.get_models()):
    b.add_model(model_name)

for i in range(2, len(sys.argv)):
    print b.get_page_annotated_version(sys.argv[i])
    if b.get_page_annotated_version(sys.argv[i]) is None:
        page_id = b.insert_new_page_annotated(sys.argv[i], 1, False, model_name, open(sys.argv[i]))
        sys.stderr.write("Inserted %s as page %d\n" % (sys.argv[i], page_id))
    else:
        sys.stderr.write("Cannot add '%s', page is already in index" % sys.argv[i])

