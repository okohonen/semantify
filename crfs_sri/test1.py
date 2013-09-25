
import string
import re
import os
from bs4 import BeautifulSoup as Soup
from bs4 import NavigableString
import devutil
import time
from sklearn.metrics import confusion_matrix

containertag=[['Korkeus noin 178cm, leveys 115cm ja syvyys 37cm', 'measures']]
i='Korkeus noin 178cm, leveys 115cm ja syvyys 37cm.'

for line in containertag:
    if line[0] in i and len(line[0])>1:
        print 'yes'
