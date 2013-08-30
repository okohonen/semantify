

import sys
import re
from collections import Counter



def compile_regexps(filename):

    # return this
    regexps = []

    for pattern in file(filename): 
        pattern = pattern.split('#')[0].strip() # discard comment after #
        if pattern != '':
            regexps.append((pattern, re.compile(pattern)))

    return regexps



regexps = compile_regexps('../../regexps/syntax_regexps.en')

words = {}

for line in file(sys.argv[1]):

    line = line.strip()

    if line:

        word, pos, tag = line.split()
    
        if not tag in words:
            
            words[tag] = Counter()
        
        else:

            words[tag][word] += 1

for tag in words.keys():
    
    print "tag:", tag

    for word, count in words[tag].items():

#        for pattern, regexp in regexps:

#            if regexp.search(word) != None: # check if active

#                print word, pattern, count

#            else:

        print word, tag, count

#        if count < 100:
#            print tag, word,  count

    raw_input("")

    print



        
        

        
        

