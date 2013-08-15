import time
from optparse import OptionParser

from models import *




if __name__ == "__main__":
 
   

    tic = time.clock()
   
    # parse options
    parser = OptionParser("Usage: %prog [options]")
    parser.add_option("--corpus", dest = "corpus_id", default = None)
    parser.add_option("--graph", dest = "graph_id", default = 'first-order-chain')
    parser.add_option("--tagset", dest = "tagset_id", default = 'BMS')
    parser.add_option("--train_algorithm", dest = "train_algorithm_id", default = 'perceptron')
    parser.add_option("--train_file", dest = "train_file", default = None)
    parser.add_option("--devel_file", dest = "devel_file", default = None)
    parser.add_option("--prediction_file", dest = "prediction_file", default = None)
    parser.add_option("--model_file", dest = "model_file", default = None)
    parser.add_option("--token_eval", action = "store_true", dest = "token_eval", default = False)
    parser.add_option("--ssl_file", dest = "ssl_file", default = None)
    parser.add_option("--verbose", action = "store_true", dest = "verbose", default = False)

    (options, args) = parser.parse_args()
   
    #print options

    print "options"
    print "\tcorpus:", options.corpus_id
    print "\tgraph:", options.graph_id
    print "\ttagset:", options.tagset_id
    print "\ttrain algorithm:", options.train_algorithm_id
    print "\ttrain file:", options.train_file    
    print "\tdevel file:", options.devel_file    
    print "\twrite optimally predicted devel set to:", options.prediction_file
    print "\tssl file:", options.ssl_file
    print "\ttoken eval:", options.token_eval
    print "\tverbose:", options.verbose
    print

    print "initialize model"
    m = Model()
    print "done"
    print
    print "train model"
    print
    m.train(options.graph_id, options.tagset_id, options.train_algorithm_id, options.train_file, options.devel_file, options.prediction_file, options.ssl_file, options.token_eval, options.verbose)      
    print "done"
    print
    print "save model"
    print "\tmodel file:", options.model_file       
    m.save(options.model_file)        
    print "done"
    print
    print "time consumed in total:", time.clock() - tic
    print
    print












    


