
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
filename='amazon100'
tagindex=20
tagset=['genre','item', 'price', 'stock', 'features']
tagdict=['WebAnnotator_genre', 'WebAnnotator_item', 'WebAnnotator_price', 'WebAnnotator_stock', 'WebAnnotator_features']


page=open(os.getcwd()+path+filename+'.html')
ret=open(os.getcwd()+path+'/temp/temp.html','w')


soup=Soup(page)

# The keywords that need to be tagged

retfile=open(os.getcwd()+path+'/temp/'+filename+'.test.prediction')
a=retfile.read().splitlines()
tokens=[]
flag=0; temptag='O';annovar=[];annotations=[]

# Obtaining annotations in the form of collocations if annotation is not a single token

for terms in a:               
    temptoken=terms.split(' : ')  
   
    if temptoken[0]:
        temptoken[0]=temptoken[0].replace('word(t)=', '')         
        temptoken[tagindex]=temptoken[tagindex].replace('1\t', '')             
        if not temptag in tagset:
            temptag=temptoken[tagindex]        
        if temptoken[tagindex] in tagset:
            if temptag==temptoken[tagindex]:
                flag=1                       
                annovar.append(temptoken[0])
                annotag=temptoken[tagindex] 
            elif  temptag in tagset:                               
                annovar=' '.join(annovar)
                annotate=[annovar, annotag]
                annotations.append(annotate)
                temptag=temptoken[tagindex]
                annovar=[]
                annovar.append(temptoken[0])
                annotag=(temptoken[tagindex]) 
        elif flag==1:
            flag=2                
            annovar=' '.join(annovar)
            annotate=[annovar, annotag]
            annotations.append(annotate)
            temptag=temptoken[tagindex]
            annovar=[]
                   
                   
            
print annotations
