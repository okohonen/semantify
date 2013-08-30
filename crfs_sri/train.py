
import time
from optparse import OptionParser

from models import *



if __name__ == "__main__":

    tic = time.clock()

    # parse options
    parser = OptionParser("Usage: %prog [options]")
    parser.add_option("--graph", dest = "graph_id", default = None)
    parser.add_option("--performance_measure_id", dest = "performance_measure_id", default = 'accuracy')
    parser.add_option("--single_pass", action = "store_true", dest = "single_pass", default = False)
    parser.add_option("--train_file", dest = "train_file", default = None)
    parser.add_option("--devel_file", dest = "devel_file", default = None)
    parser.add_option("--devel_prediction_file", dest = "devel_prediction_file", default = None)
    parser.add_option("--model_file", dest = "model_file", default = None)
    parser.add_option("--verbose", action = "store_true", dest = "verbose", default = False)

    (options, args) = parser.parse_args()

    # print options

    print
    print "options"
    print "\tperformance measure:", options.performance_measure_id
    print "\tsingle pass:", options.single_pass
    print "\ttrain file:", options.train_file
    print "\tdevel file:", options.devel_file
    print "\tdevel prediction file:", options.devel_prediction_file
    print "\tverbose:", options.verbose
    print
    print "initialize model"
    m = Model()
    print "done"
    print
    print "train model"
    m.train(options.graph_id,
            options.performance_measure_id,
            options.single_pass, 
            options.train_file, 
            options.devel_file, 
            options.devel_prediction_file, 
            options.verbose)
    print "done"
    print
    print "save model"
    m.save(options.model_file)
    print "done"
    print
    print "time consumed in total:", time.clock() - tic
    print
