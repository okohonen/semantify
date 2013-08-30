
import time
from optparse import OptionParser

from models import *

if __name__ == "__main__":

    tic = time.clock()

    # parse options
    parser = OptionParser("Usage: %prog [options]")
    parser.add_option("--corpus", dest = "corpus_id", default = None)
    parser.add_option("--task", dest = "task_id", default = None)

    parser.add_option("--model_file", dest = "model_file", default = None)
    parser.add_option("--test_file", dest = "test_file", default = None)
    parser.add_option("--prediction_file", dest = "prediction_file", default = None)
    parser.add_option("--reference_file", dest = "reference_file", default = None)    
    parser.add_option("--verbose", action = "store_true", dest = "verbose", default = False)


    (options, args) = parser.parse_args()

    print "options"
    print "\tmodel file:", options.model_file
    print "\ttest file:", options.test_file
    print "\treference file:", options.reference_file
    print "\tprediction file:", options.prediction_file
    print "\tverbose:", options.verbose    
    print
    print "initialize model"
    m = Model()
    print "done"
    print
    print "load model"
    m.load(options.model_file)
    print "done"
    print
    print "apply"
    m.apply(options.test_file, options.prediction_file, options.reference_file, options.verbose)
    print "done"
    print
    print "time consumed in total:", time.clock() - tic
    print



