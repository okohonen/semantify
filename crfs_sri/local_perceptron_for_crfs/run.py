
import time
from optparse import OptionParser

from models import *



if __name__ == "__main__":

    tic = time.clock()

    # parse options
    parser = OptionParser("Usage: %prog [options]")
    parser.add_option("--corpus", dest = "corpus_id", default = None)
    parser.add_option("--task", dest = "task_id", default = None)
    parser.add_option("--graph", dest = "graph_id", default = None)
    parser.add_option("--train_algorithm", dest = "train_algorithm_id", default = None)
    parser.add_option("--inference", dest = "inference_id", default = None)
    parser.add_option("--single_pass", action = "store_true", dest = "single_pass", default = False)
    parser.add_option("--train_file", dest = "train_file", default = None)
    parser.add_option("--devel_file", dest = "devel_file", default = None)
    parser.add_option("--devel_prediction_file", dest = "devel_prediction_file", default = None)
    parser.add_option("--model_file", dest = "model_file", default = None)
    parser.add_option("--test_file", dest = "test_file", default = None)
    parser.add_option("--test_prediction_file", dest = "test_prediction_file", default = None)
    parser.add_option("--test_reference_file", dest = "test_reference_file", default = None)    
    parser.add_option("--verbose", action = "store_true", dest = "verbose", default = False)

    (options, args) = parser.parse_args()

    # print options

    print
    print "options"
    print "\tcorpus:", options.corpus_id
    print "\ttask:", options.task_id
    print "\tgraph:", options.graph_id
    print "\ttrain algorithm:", options.train_algorithm_id
    print "\tinference:", options.inference_id
    print "\tsingle pass:", options.single_pass
    print "\ttrain file:", options.train_file
    print "\tdevel file:", options.devel_file
    print "\tdevel prediction file:", options.devel_prediction_file
    print "\ttest file:", options.test_file
    print "\ttest prediction file:", options.test_prediction_file
    print "\ttest reference file:", options.test_reference_file
#    print "\ttrain data set size:", options.train_set_size
    print "\tverbose:", options.verbose
    print
    print "initialize model"
    m = Model()
    print "done"
    print
    print "train model"
    m.train(options.corpus_id, 
            options.task_id, 
            options.graph_id,
            options.train_algorithm_id, 
            options.inference_id,
            options.single_pass, 
            options.train_file, 
            options.devel_file, 
            options.devel_prediction_file, 
#             options.train_set_size,
            options.verbose)
    print "done"
    print
    print "save model"
    m.save(options.model_file)
    print "done"
    print
    print "apply model"
    m.apply(options.test_file, options.test_prediction_file, options.test_reference_file, options.verbose)
    print "done"
    print
    print "time consumed in total:", time.clock() - tic
    print