

import time
import numpy
import sys
from optparse import OptionParser
from collections import Counter



def train(train_file, token, coltekin):

    varieties = {'successor' : {}, 'predecessor' : {}}

    for line in file(train_file):

        if token:
            word, count = line.strip().split()
        else:
            word = line.strip()

        word_ = word + '_'

        for t in range(1, len(word_)):

            prefix = word_[:t]
            successor = word_[t]

            if prefix in varieties['successor']:

                varieties['successor'][prefix][successor] += 1

            else:

                varieties['successor'][prefix] = Counter()
                varieties['successor'][prefix][successor] += 1                                   
                
        word_ = word[::-1] + '_'
        
        for t in range(1, len(word_)):

            suffix = word_[:t]
            predecessor = word_[t]

            if suffix in varieties['predecessor']:

                varieties['predecessor'][suffix][predecessor] += 1

            else:

                varieties['predecessor'][suffix] = Counter()
                varieties['predecessor'][suffix][predecessor] += 1                    

    if coltekin:

        coltekin_counts = {'successor' : Counter(), 'predecessor' : Counter()}
        num_prefixes_of_len = Counter()
        num_suffixes_of_len = Counter()
        
        for prefix, successors in varieties['successor'].items():

            coltekin_counts['successor'][len(prefix)] += len(successors)
            num_prefixes_of_len[len(prefix)] += 1

        for prefix_len, num in coltekin_counts['successor'].items():

            coltekin_counts['successor'][prefix_len] = float(num)/num_prefixes_of_len[prefix_len]

        for suffix, predecessors in varieties['predecessor'].items():

            coltekin_counts['predecessor'][len(suffix)] += len(predecessors)
            num_suffixes_of_len[len(suffix)] += 1

        for suffix_len, num in coltekin_counts['predecessor'].items():

            coltekin_counts['predecessor'][suffix_len] = float(num)/num_suffixes_of_len[suffix_len]

    model = {'successor' : {}, 'predecessor' : {}}

    for prefix, successors in varieties['successor'].items():

        if coltekin:

            model['successor'][prefix] = len(successors)/coltekin_counts['successor'][len(prefix)]

        else:

            model['successor'][prefix] = len(successors)

    for suffix, predecessors in varieties['predecessor'].items():

        if coltekin:

            model['predecessor'][suffix] = len(predecessors)/coltekin_counts['predecessor'][len(suffix)]

        else:

            model['predecessor'][suffix] = len(predecessors)

    return model


def apply(input_file, output_file, varieties):

    OUTPUT = open(output_file, 'w')

    for word in file(input_file):
        
        word = word.strip()

        line = word + ' SV' 

        word_ = word + '_'

        for t in range(1, len(word_)):

            prefix = word_[:t]
            successor = word_[t]

            if prefix in model['successor']:

                sv = model['successor'][prefix]

            else:

                sv = 0
                
            line += ' ' + str(sv)
            
        OUTPUT.write('%s\n' % line)

#        print "sv:", line

        word_ = word[::-1] + '_'
        
#    OUTPUT.close()
#    OUTPUT = open(output_file + '.pv', 'w')

    for word in file(input_file):

        word = word.strip()

        word_ = word[::-1] + '_'

        line = ''

        for t in range(1, len(word_)):

            suffix = word_[:t]
            predecessor = word_[t]

            if suffix in model['predecessor']:

                pv = model['predecessor'][suffix]
 
            else:

                pv = 0
        
            line = str(pv) + ' ' + line

        line = word + ' PV ' + line

        OUTPUT.write('%s\n' % line)

#        print "pv:", line

    OUTPUT.close()

    return




if __name__ == "__main__":

    tic = time.clock()

    # parse options
    parser = OptionParser("Usage: %prog [options]")
    parser.add_option("--train_file", dest = "train_file", default = None)
    parser.add_option("--model_file", dest = "model_file", default = None)
    parser.add_option("--input_file", dest = "input_file", default = None)
    parser.add_option("--output_file", dest = "output_file", default = None)
    parser.add_option("--token", action = "store_true", dest = "token", default = False)
    parser.add_option("--coltekin", action = "store_true", dest = "coltekin", default = True)
    parser.add_option("--verbose", action = "store_true", dest = "verbose", default = False)

    (options, args) = parser.parse_args()

    # print options
    
    print "train file:", options.train_file
    print "model file:", options.model_file
    print "input file:", options.input_file
    print "output file:", options.output_file
    print "word tokens:", options.token
    print "coltekin:", options.coltekin
    print "verbose:", options.verbose

    # count varieties

    if options.train_file:

        model = train(options.train_file, options.token, options.coltekin)

        if options.model_file:

            pass # save

    else:

        pass # load
        
    # apply to data

    if options.input_file and options.output_file:

        apply(options.input_file, options.output_file, model)


    print "time consumed:", time.clock() - tic

    
    

    
    



    
    
    
