import sys
import backend
from crfs import *
import argparse
import devutil
import gzip
import incremental_training as it
import feature_file as ff
from bs4 import BeautifulSoup
import htmlparse as hp

# This script trains a model incrementally and decodes the test set after training on each model

b = backend.Backend()

parser = argparse.ArgumentParser(
        prog='train_model_incremental.py',
        description="Calls the incremental training routines used in actual system usage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False)

# Options for input data files

parser.add_argument('-n', '--nr-of-folds', dest="nrfolds", default=None, type=int, help="number of crossvalidation folds to base train-test split on")
parser.add_argument('-f', '--fold', dest="fold", default=None, type=int, help="active fold")
parser.add_argument('-s', '--feature-set', dest="feature_set", default=None, help="feature_set")
parser.add_argument('-o', '--output-file-pattern', dest="output_pattern", default="out", help="output file pattern")
parser.add_argument('-m', '--model-name', dest="model_name", default=None, help="model_name")

args = parser.parse_args(sys.argv[2:])

file_list = eval(open(sys.argv[1]).read())
assert(type(file_list) is list)

test_reference_file = "%s.test.reference.gz" % args.output_pattern
test_file = "%s.test.gz" % args.output_pattern
devel_prediction_file = "%s.devel.prediction" % args.output_pattern
test_prediction_name = "%s.test.prediction" % args.output_pattern
final_model = "%s_model.bin" % args.output_pattern

verbose = True

filename = "data/temp/train.log"

# Training test split
training_set, test_set = backend.k_fold_cross_validation(file_list, args.nrfolds, args.fold-1)
b.build_data_set(args.model_name, test_reference_file, test_set, args.feature_set);
print "Creating test file '%s'\n" % test_file
b.striplabel(test_reference_file, test_file)

model_training = it.TrainingFileBuilderIncrementalTraining(".", args.output_pattern, it.ModuloTrainDevelSplitter(10))
model_training.set_verbose(True)

for i in range(len(training_set)):
    model_file = devel_prediction_file = "%s_%d_model.bin" % (args.output_pattern, i+1)

    # Preprocess_file
    parsed_page = hp.parse_page(BeautifulSoup(gzip.open(training_set[i])), args.feature_set, annotated=True, build_node_index=False)
    # Add to incremental training set
    model_training.incremental_train(parsed_page.read_features(), devel_prediction_file, model_file)
    model_training.apply(model_file, test_file, "%s_%d_test.prediction" % (args.output_pattern, i+1))
