import sys
import backend
import argparse
import devutil

b = backend.Backend()

parser = argparse.ArgumentParser(
        prog='make_data_set.py',
        description="Creates data set from a list of indexed source files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False)

# Options for input data files
parser.add_argument('-n', '--nr-of-folds', dest="nrfolds", default=None, type=int, help="number of crossvalidation folds")
parser.add_argument('-f', '--fold', dest="fold", default=None, type=int, help="active fold")
parser.add_argument('-s', '--feature-set', dest="feature_set", default=None, help="feature_set")
parser.add_argument('-o', '--output-file-pattern', dest="output_pattern", default=None, help="output file pattern")
parser.add_argument('-m', '--model-name', dest="model_name", default=None, help="model_name")

args = parser.parse_args(sys.argv[2:])

file_list = eval(open(sys.argv[1]).read())
assert(type(file_list) is list)

train_file = "%s.train.gz" % args.output_pattern
devel_file = "%s.devel.gz" % args.output_pattern
test_file = "%s.test.gz" % args.output_pattern
test_reference_file = "%s.test.reference.gz" % args.output_pattern

b.make_experiment_datasets(file_list, args.model_name, train_file, devel_file, test_reference_file, test_file, args.feature_set, args.nrfolds, args.fold-1)
