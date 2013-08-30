

import sys
import re
from collections import Counter

previous_tag = 'None'

for line in file(sys.argv[1]):

    line = line.strip()

    if line:

        word, pos, tag = line.split()
    
        if tag[0] == 'B' and previous_tag == tag:

            print previous_tag
            print tag

        previous_tag = tag

            

    else:

        previous_tag = 'None'

        print

        
        

