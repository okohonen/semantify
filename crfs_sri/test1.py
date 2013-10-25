
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

path='/data/amazon/'
filename='amazon052'
tagindex=20
tagset=['genre','item', 'price', 'stock', 'features']
tagdict=['WebAnnotator_genre', 'WebAnnotator_item', 'WebAnnotator_price', 'WebAnnotator_stock', 'WebAnnotator_features']



page=open(os.getcwd()+path+filename+'.html')

soup=Soup(page)
reg=re.compile('WebAnnotator_[a-zA-Z0-9]')
tagdict=[]; tagset=[]
taglist= soup.find_all('span', class_=reg)
for index in taglist:
    index=str(index).split('"')
    if not index[1] in tagdict:
        tagdict.append(index[1])
        tagtemp=index[1].replace('WebAnnotator_', '')
        tagset.append(tagtemp)
        
print tagdict, tagset
    


    

