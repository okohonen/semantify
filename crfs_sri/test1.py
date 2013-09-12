
import string
import re
import os
from bs4 import BeautifulSoup as Soup
from bs4 import NavigableString
import devutil
import time
from sklearn.metrics import confusion_matrix

filename='snippetfile'
experiment='experiment80'
confusion='confusion80'

predictionfile=open(os.getcwd()+'/temp/'+filename+'.'+experiment+'.prediction.tracker')

confusionfile=open(os.getcwd()+'/temp/'+filename+'.'+confusion+'.confusion', 'w')



prediction=predictionfile.read().splitlines()
true=[]; predfull=[]
pred=[]

def replace(token):
    if 'home' in token:
        token=1        
    elif 'away' in token:
        token=2        
    elif 'score' in token:
        token=3
    elif 'date' in token:
        token=4
    else:
        token=0
    return token

for i in range(len(prediction)):
    line=prediction[i].split('\t')   
    line[0]=replace(line[0])
    line[1]=replace(line[1])
    line[2]=replace(line[2])
    true.append(line[0])
    predfull.append(line[1])
    pred.append(line[2])
    confusionfile.write(repr(line))
    confusionfile.write('\n')
    
    
print confusion_matrix(true, pred)


confusionfile.close()


 





