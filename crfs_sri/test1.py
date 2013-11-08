
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
filename='amazon098'
tagindex=20
tagset=['genre','item', 'price', 'stock', 'features']
tagdict=['WebAnnotator_genre\nWebAnnotator_item\nWebAnnotator_price"\n"WebAnnotator_stock"\n"WebAnnotator_features']

page=open(os.getcwd()+path+filename+'.html','r')     
soup=Soup(page)

for i in soup.body.descendants:     			
    if isinstance(i,NavigableString): 
        instring= i
        instringsplit=[]
        if len(instring)<80 and len(instring)>1:            
            instringsplit.append([element for element in instring.split('.')])
            p=[p.split() for p in instringsplit[0]]
            for m in p:
                print m
             
      

