#!/usr/bin/env python

from __future__  import division
import socket
import urllib2
import sqlite3
import os
import string
import re
import time
from bs4 import BeautifulSoup as Soup
from bs4 import NavigableString
from datetime import datetime
import shlex, subprocess
import sys  
from sklearn.metrics import confusion_matrix


        

def iscapital(token):
    tokensplit=list(token)    
    if  re.match('[A-Z]', tokensplit[0]) :
        return "1"
    else:
        return "0"


def isnumber(token):    
    if   not re.match('[^0-9]', token):
        return "1"
    else:
        return "0"


def hasnumber(token):    
    if   re.match('[0-9]', token):
        return "1"
    else:
        return "0"


def hassplchars(token):
    if   not re.match('[a-zA-Z0-9]', token):
        return "1"
    else:
        return "0"  

def hasFC(token):
    if 'FC' in token:
        return "1"
    else:
        return "0"
        
def generalisation(token):
    reg1=re.compile('[A-Z]')
    reg2=re.compile('[a-z]')
    reg3=re.compile('[0-9]')
    reg4=re.compile('[^A-Za-z0-9]')
    long=[]
    for i in range(len(token)):
        if re.match(reg1, token[i]):
            long.append('A')
        elif re.match(reg2, token[i]):
            long.append('a')
        elif re.match(reg3, token[i]):
            long.append('1')
        elif re.match(reg4, token[i]):
            long.append('#')
    brief=[];    
    temp=long[0]    
    for i in range(len(long)):        
        if not temp== long[i]:
            brief.append(temp)
            temp=long[i]
    brief.append(temp)     
    long=''.join(long)
    brief=''.join(brief)
    return long, brief
        
        
def preprocess(filename, experiment, tagset,  tagdict,  factor,  tagindex):        
    
    conn = sqlite3.connect('sentence.db')
    c = conn.cursor()
    

    page=open(os.getcwd()+'/temp/'+filename+'.html','r') 
    trainfile=open(os.getcwd()+'/temp/'+filename+'.train','w')
    traindevelfile=open(os.getcwd()+'/temp/'+filename+'.train.devel','w')    
    testfile = open(os.getcwd()+'/temp/'+filename+'.test','w')    
    testreferencefile = open(os.getcwd()+'/temp/'+filename+'.test.reference','w')
    soup=Soup(page)   
    counter=0
    tokens=[];    parentname=[];    tags=[];    devels=[];  test=[];    testreference=[];   tagscount=0;    
    containertag=['a','b','c'];  previousterm=['na']; ancestors=[]
    capital=[];number=[]; h_number=[];splchars=[];long=[]; brief=[]; classlong=[]; classbrief=[]; tagsetname=[];parentsname=[]
  

    

    for i in soup.body.descendants:     			
        if isinstance(i,NavigableString):    
            instring=re.sub('[^a-zA-Z0-9\.\-?]', ' ', i)              
            if len(instring)<50 and len(instring)>1:                
                iterator=0;parentname=[]; ancestor=[]
                for parent in i.parents:
                    iterator=iterator+1 
                    if parent.name: 
                        if parent.name=='html':
                            break
                        else:
                            ancestor.append(parent.name)
                            if  iterator<4:
                                parentname.append(parent.name) 
                if len(parentname)<3:
                    for count in range(0, 4):
                        if len(parentname)<3:
                            parentname.append('na')                            
           
                instringsplit=instring.split()
                for m in instringsplit:
                    
                    
                    ancestors='-'.join(ancestor)    
                    parentsname.append(parentname)
                                      
                    # Feature extraction
                    capital.append(iscapital(m))
                    number.append(isnumber(m))                                                                          
                    h_number.append(hasnumber(m))                       
                    splchars.append(hassplchars(m)) 
                    longtemp, brieftemp=generalisation(m)  
                    long.append(longtemp)
                    brief.append(brieftemp)                  
                    classname=re.findall('class=".*"', containertag)
                    if classname:
                        classname=classname[0].split('=')
                        classname=repr(re.sub('"', '', classname[1]))
                        classlongtemp, classbrieftemp=generalisation(classname)
                        classnames.append(classname)
                        classlong.append(classlongtemp)
                        classbrief.append(classbrieftemp)
                    else:
                        classname='na'
                        classlongtemp, classbrieftemp="A", "B"
                        classnames.append(classname)
                        classlong.append(classlongtemp)
                        classbrief.append(classbrieftemp)
                    
                    #print  previousterm, m, capital,  number,  h_number,  splchars,  long, brief,  classname,  classlong,  classbrief,  parentname[0],  parentname[1],  parentname[2],  ancestors
                    
                   
                    if parentname[0]=='span':
                        if  tagdict[0]in containertag:   
                             tagsetname.append(tagset[0])                     
                        elif  tagdict[1] in containertag:              
                             tagsetname.append(tagset[1])
                        elif  tagdict[2] in containertag:
                             tagsetname.append(tagset[2])                           
                        elif  tagdict[3] in containertag: 
                             tagsetname.append(tagset[3])
                        else:
                            tagsetname.append('O')
                    else:                                 
                        tagsetname.append('O')         
                    
                    if counter>1:
                        tags.append('word(t)='+m+' : 1\tiscapital : '+capital[counter-1]+'\tisnumber : '+number[counter-1]+'\thasnumber : '+h_number[counter-1]+'\thassplchars : '+splchars[counter-1]+'\tlong(t)='+long[counter-1]+' : 1\tbrief(t)='+brief[counter-1]+' : 1\tclassname(t)='+classnames[counter-1]+' : 1\tclasslong(t)='+classlong[counter-1]+' : 1\tclassbrief(t)='+classbrief[counter-1]+' : 1\tparentname(t)='+parentsname[counter-1][0]+' : 1\tgrandparentname(t)='+parentsname[counter-1][1]+' : 1\tgreatgrandparentname(t)='+parentsname[counter-1][2]+' : 1\tancestors(t)='+ancestors[counter-1]+' : 1\t'+tagsetname[counter-1]+'\n') 
                        test.append('word(t)='+m+' : 1\tiscapital : '+capital[counter-1]+'\tisnumber : '+number[counter-1]+'\thasnumber : '+h_number[counter-1]+'\thassplchars : '+splchars[counter-1]+'\tlong(t)='+long[counter-1]+' : 1\tbrief(t)='+brief[counter-1]+' : 1\tclassname(t)='+classnames[counter-1]+' : 1\tclasslong(t)='+classlong[counter-1]+' : 1\tclassbrief(t)='+classbrief[counter-1]+' : 1\tparentname(t)='+parentsname[counter-1][0]+' : 1\tgrandparentname(t)='+parentsname[counter-1][1]+' : 1\tgreatgrandparentname(t)='+parentsname[counter-1][2]+' : 1\tancestors(t)='+ancestors[counter-1]+' : 1\t\n') 
                        if  counter%10==0:
                            tags.append('\n')
                            test.append('\n')
                       
                             
                    # previous and prepreviousterms
                    previousterm.append(m)
                    counter=counter+1
                    
        containertag=i.encode('utf8')
        
        
        
   
    linetags=[]; temp=[]; temptags=[] 
    
  
   
    # Cleaning out useless 'O' tags and maintaining only the ones within +/-6 tags limit for learning the transitions from 'O' to annotation value
    flag=0
    for i in range(len(tags)):
        temp=tags[i].split(' : ')        
        if temp[0]=='\n':            
            newline=newline+1
        else:
            temp[tagindex]=temp[tagindex].replace('1\t', '')
            temp[tagindex]=temp[tagindex].replace('\n', '')
            if temp[tagindex] in tagset:               
                temptags.append(tags[i])
                if flag==0:
                    temp[tagindex]
                    firsttagindex=i
                    flag=1
            else:
                counter=0
                for j in range(10):
                    if  (i+j) <len(tags):                                              
                        temp=tags[i+j].split(' : ')
                        if not temp[0]=='\n':
                            temp[tagindex]=temp[tagindex].replace('1\t', '')
                            temp[tagindex]=temp[tagindex].replace('\n', '')
                            if temp[tagindex] in tagset: 
                                temptags.append(tags[i])
                                break
                            else:
                                counter=counter+1
                                if counter>8:
                                    break
                    else:
                        break
                        
   
    
    
    counter=0; newtags=[]
    for i in range(len(temptags)):
        newtags.append(temptags[i])   
        if i%10==0:
            newtags.append('\n')  
            
           
    #                 Experiment 1: feeding 10% of the training data and producing test accuracy         
    
    experimenttrain=open(os.getcwd()+'/temp/'+filename+'.'+experiment+'.train', 'w')
    experimentdevel=open(os.getcwd()+'/temp/'+filename+'.'+experiment+'.train.devel', 'w')
    
    counter=0; experiment10=int((len(newtags)*factor))
    print 'No of lines in experiment set:',  experiment10
    for i in range(len(tags)):             
        counter=counter+1
        trainfile.write(tags[i])        
        if counter%10==0:
            traindevelfile.write(tags[i])
    counter=0
    for j in range(firsttagindex, firsttagindex+experiment10): 
        counter=counter+1
        experimenttrain.write(tags[j])
        if counter%10==0:
            experimentdevel.write(tags[j])
        
    trainfile.close()   
    traindevelfile.close() 
    experimenttrain.close()
    experimentdevel.close()

    '''                    
    counter=0
    for i in range(len(newtags)):
        counter=counter+1
        trainfile.write(newtags[i])
        if counter%10==0:
            traindevelfile.write(newtags[i])
    trainfile.close()   
    traindevelfile.close() 
    '''       
    counter=0
    for i in range(len(test)):
        counter=counter+1
        testfile.write(test[i])
        if counter%10==0:
            testreferencefile.write(test[i])
    testfile.close()
    testreferencefile.close()
    
    print len(tags),  len(temptags),  len(newtags)       
    return 1
    
    
def keywordtag(filename, tagset,  tagdict,  tagindex):
    starttime=time.time()
    # Reference snippet to apply return tags to the html file
    page=open(os.getcwd()+'/temp/'+filename+'.html')
    ret=open(os.getcwd()+'/temp/temp.html','w')


    soup=Soup(page)

    # The keywords that need to be tagged
    
    retfile=open(os.getcwd()+'/temp/'+filename+'.test.prediction')
    a=retfile.read().splitlines()
    tokens=[]
    flag=0; temptag='O';annovar=[];annotations=[]
    
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
                elif  flag==1:
                    flag=2                
                    annovar=' '.join(annovar)
                    annotate=[annovar, annotag]
                    annotations.append(annotate)
                    temptag=temptoken[tagindex]
                    annovar=[]  
            elif flag==1:
                flag=2                
                annovar=' '.join(annovar)
                annotate=[annovar, annotag]
                annotations.append(annotate)
                temptag=temptoken[tagindex]
                annovar=[]
                       
                

   
    print annotations
            
    # This chunk of code checks through the descendants for presence of NavigableStrings and replaces the string with an 'a' with title=keyword for tooltip purpose.
    w=soup

    for line in annotations:
        for child in w.descendants:
            if child.next_sibling:
                for i in child.next_sibling:           
                    if isinstance(i,NavigableString):                           
                        if len(i)<50 and len(i)>0:                        
                                if line[0] in i and len(line[0])>1:                           
                                    if i.parent.name=='a':
                                        i.parent['title']=line[1]; i.parent['style']="color:#000000; background-color:#40E0D0"                            
                                    elif i.parent.name=='span' and [k in containertag for k in tagdict]:                                        
                                        continue
                                    else:                                        
                                        reg=re.compile(line[0])  
                                        match=re.search(reg,i)
                                        start, end = match.start(), match.end()      				
                                        newtag=i[:start]+'<span style="color:#000000; background-color:#40E0D0" title="'+line[1]+'">'+line[0]+'</span>'+i[end:]				
                                        i.string.replace_with(newtag)
                    containertag=i                    

    
    for i in soup:		
        ret.write(repr(i))
        
    lt='&lt;' ; gt='&gt;'

    page.close()
    ret.close()

    # Since Beautifulsoup uses unicode, work around here is opening the temp file and replacing the tags with appropriate '<','>' and saving the file.

    fin = open(os.getcwd()+'/temp/temp.html')
    fout = open(os.getcwd()+'/temp/'+filename+'tagged.html', 'w')
    content=[]
    for line in fin:
        if lt in line or gt in line:
            line=line.replace('&lt;','<')    
            line=line.replace('&gt;','>')
            line=line.replace('<html><body>', '')
            line=line.replace('</body></html>', '')
            fout.write(line)
            content.append(line)
        else:
            fout.write(line)
            content.append(line)
    fin.close()
    fout.close()
    return content
        


def confusionmatrix(filename, experiment, confusion,  tagset):

    predictionfile=open(os.getcwd()+'/temp/'+filename+'.'+experiment+'.prediction.tracker')
    
    confusionfile=open(os.getcwd()+'/temp/'+filename+'.'+confusion+'.confusion', 'w')    
    
    
    prediction=predictionfile.read().splitlines()
    true=[]; predfull=[]
    pred=[]
    
    def replace(token):
        if tagset[0] in token:
            token=1        
        elif tagset[1] in token:
            token=2        
        elif tagset[2] in token:
            token=3
        elif tagset[3] in token:
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
    
    confusionfile.close()    
    
    print  'Confusion matrix for', experiment, 'model is :', confusion_matrix( predfull,  true)
    print  'Confusion matrix for', experiment, 'model is :', confusion_matrix(pred,  true)

    return 
    


def accuracy(filename,  experiment,  tagindex):
    
    standardfile=open(os.getcwd()+'/temp/'+filename+'.train')
    firstfile=open(os.getcwd()+'/temp/'+filename+'.test.prediction')
    secondfile=open(os.getcwd()+'/temp/'+filename+'.'+experiment+'.test.prediction')
    predictiontracker=open(os.getcwd()+'/temp/'+filename+'.'+experiment+'.prediction.tracker', 'w')
    
    standard=standardfile.read().splitlines()
    stan=[]
    for i in standard:
        line=i.split(' : ')
        if line[0] and not line[0]=='\n':
            line=line[tagindex].replace('1\t', '')
            line=line.replace('\n', '')
            stan.append(line)
        
    first=firstfile.read().splitlines()
    file1=[]
    for i in first:
        line=i.split(' : ')
        if line[0] and not line[0]=='\n':
            line=line[tagindex].replace('1\t', '')
            line=line.replace('\n', '')
            file1.append(line)
        
    second=secondfile.read().splitlines()
    file2=[]
    for i in second:
        line=i.split(' : ')
        if line[0] and not line[0]=='\n':
            line=line[tagindex].replace('1\t', '')
            line=line.replace('\n', '')
            file2.append(line)
        
    print 'Length of stan, file1, file2:', len(stan), len(file1), len(file2)
    a=0; b=0
    for i in range(len(stan)):
        if stan[i]==file1[i]:
            a=a+1
        if stan[i]==file2[i]:
            b=b+1
        predictiontracker.write(stan[i]); predictiontracker.write('\t')
        predictiontracker.write(file1[i]); predictiontracker.write('\t')
        predictiontracker.write(file2[i]); predictiontracker.write('\t')
        predictiontracker.write('\n')
    predictiontracker.close()
            

    
    f1=(a/len(stan))*100
    print 'Original model accuracy is : ', f1
    
    f2=(b/len(stan))*100
    print  experiment,'model accuracy is :', f2
    
    return
    
    
    
    
    
    
    
    
    
    
    
    
    
