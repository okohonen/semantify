
import string
import re
import os
from bs4 import BeautifulSoup as Soup
from bs4 import NavigableString
import devutil
import time
from sklearn.metrics import confusion_matrix
import numpy
import sqlite3
import devutil

path='/data/application/'
filename='adorationtemp'


page=open(os.getcwd()+path+filename+'.html','r')     
soup=Soup(page)
htmltags=['a', 'abbr', 'b', 'basefont', 'bdo', 'big', 'br', 'dfn', 'em', 'font', 'i', 'img', 'input', 'kbd', 'label', 'q', 's', 'samp', 'select', 'small', 'span', 'strike', 'strong', 'sub', 'sup', 'textarea', 'tt', 'u', 'var']

allstrings=[] 


for i in soup.body.descendants:
    if not type(i) is None and isinstance(i,  NavigableString):
        if len(i)>1 and i.parent.name in htmltags:
            print i
