import sys
import backend

# Usage add_files_to_index.py model_name 

b = backend.Backend()

model_name = sys.argv[1]

train_file = "data/temp/%s.train.gz" % model_name
devel_file = "data/temp/%s.devel.gz" % model_name
test_file = "data/temp/%s.test.gz" % model_name
test_reference_file = "data/temp/%s.test.reference.gz" % model_name

b.make_experiment_datasets(train_file, devel_file, test_reference_file, test_file, model_name, "ortho3+html1")
