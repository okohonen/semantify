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


        

def iscapital(token):
    tokensplit=list(token)    
    if  re.match('[A-Z]', tokensplit[0]) :
        return True
    else:
        return False


def isnumber(token):    
    if   not re.match('[^0-9]', token):
        return True
    else:
        return False


def hasnumber(token):    
    if   re.match('[0-9]', token):
        return True
    else:
        return False


def hassplchars(token):
    if   not re.match('[a-zA-Z0-9]', token):
        return True
    else:
        return False  

def hasFC(token):
    if 'FC' in token:
        return True
    else:
        return False

    
        
        
def preprocess(filename, experiment, tagset,  tagdict):        
    
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
    containertag=['a','b','c']
    
  
    
    

    for i in soup.body.descendants:     			
        if isinstance(i,NavigableString):    
            instring=re.sub('[^a-zA-Z0-9\.\-?]', ' ', i)              
            if len(instring)<50 and len(instring)>1:
                counter=counter+1
                iterator=0;parentname=[]
                for parent in i.parents:
                    iterator=iterator+1
                    if iterator<3:
                        parentname.append(parent.name)                                     
                instringsplit=instring.split()
                for m in instringsplit:
                    if iscapital(m):
                            capital="1"
                    else:
                        capital="0"
                    if isnumber(m):
                        number="1"
                    else:
                        number="0"
                    if hasnumber(m):
                        h_number="1"
                    else:
                        h_number="0"
                    if hassplchars(m):
                        splchar="1"
                    else:
                        splchars="0"  
                    if hasFC(m):
                        has_fc="1"
                    else:
                        has_fc="0"
                    if len(containertag)<2:
                        pass
                    if parentname[0]=='span':            
                        if  tagdict[0] in str(containertag) or tagdict[0] in str(precontainertag):                            
                            c.execute('''insert into sentences (entity, tag, added) VALUES (?,?,?)''',(m,tagset[0],  datetime.now())) 
                            conn.commit()   
                            tags.append ('word(t)='+m+' : 1\tiscapital : '+capital+'\tisnumber : '+number+'\thasnumber : '+h_number+'\thassplchars : '+splchars+'\thas_fc : '+has_fc+'\tparentname(t)='+parentname[0]+' : 1\tgrandparentname(t)='+parentname[1]+' : 1\t'+tagset[0]+'\n') 
                            test.append ('word(t)='+m+' : 1\tiscapital : '+capital+'\tisnumber : '+number+'\thasnumber : '+h_number+'\thassplchars : '+splchars+'\thas_fc : '+has_fc+'\tparentname(t)='+parentname[0]+' : 1\tgrandparentname(t)='+parentname[1]+' : 1\t\n') 
                            tagscount=tagscount+1
                            if tagscount%10==0:
                                 tags.append('\n')
                                 
                        elif tagdict[1] in str(containertag) or tagdict[1] in str(precontainertag):                   
                            c.execute('''insert into sentences (entity, tag, added) VALUES (?,?,?)''',(m,tagset[1],  datetime.now())) 
                            conn.commit()   
                            tags.append ('word(t)='+m+' : 1\tiscapital : '+capital+'\tisnumber : '+number+'\thasnumber : '+h_number+'\thassplchars : '+splchars+'\thas_fc : '+has_fc+'\tparentname(t)='+parentname[0]+' : 1\tgrandparentname(t)='+parentname[1]+' : 1\t'+tagset[1]+'\n') 
                            test.append ('word(t)='+m+' : 1\tiscapital : '+capital+'\tisnumber : '+number+'\thasnumber : '+h_number+'\thassplchars : '+splchars+'\thas_fc : '+has_fc+'\tparentname(t)='+parentname[0]+' : 1\tgrandparentname(t)='+parentname[1]+' : 1\t\n') 
                            tagscount=tagscount+1
                            if tagscount%10==0:
                                 tags.append('\n')
                                 
                        elif tagdict[2] in str(containertag) or tagdict[2] in str(precontainertag):                             
                            c.execute('''insert into sentences (entity, tag, added) VALUES (?,?,?)''',(m,tagset[2],  datetime.now())) 
                            conn.commit()   
                            tags.append ('word(t)='+m+' : 1\tiscapital : '+capital+'\tisnumber : '+number+'\thasnumber : '+h_number+'\thassplchars : '+splchars+'\thas_fc : '+has_fc+'\tparentname(t)='+parentname[0]+' : 1\tgrandparentname(t)='+parentname[1]+' : 1\t'+tagset[2]+'\n') 
                            test.append ('word(t)='+m+' : 1\tiscapital : '+capital+'\tisnumber : '+number+'\thasnumber : '+h_number+'\thassplchars : '+splchars+'\thas_fc : '+has_fc+'\tparentname(t)='+parentname[0]+' : 1\tgrandparentname(t)='+parentname[1]+' : 1\t\n') 
                            tagscount=tagscount+1
                            if tagscount%10==0:
                                 tags.append('\n')
                            
                        elif tagdict[3] in str(containertag) or tagdict[3] in str(precontainertag): 
                            c.execute('''insert into sentences (entity, tag, added) VALUES (?,?,?)''',(m,tagset[3],  datetime.now())) 
                            conn.commit()   
                            tags.append ('word(t)='+m+' : 1\tiscapital : '+capital+'\tisnumber : '+number+'\thasnumber : '+h_number+'\thassplchars : '+splchars+'\thas_fc : '+has_fc+'\tparentname(t)='+parentname[0]+' : 1\tgrandparentname(t)='+parentname[1]+' : 1\t'+tagset[3]+'\n') 
                            test.append ('word(t)='+m+' : 1\tiscapital : '+capital+'\tisnumber : '+number+'\thasnumber : '+h_number+'\thassplchars : '+splchars+'\thas_fc : '+has_fc+'\tparentname(t)='+parentname[0]+' : 1\tgrandparentname(t)='+parentname[1]+' : 1\t\n') 
                            tagscount=tagscount+1
                            if tagscount%10==0:
                                 tags.append('\n')
                                 
                    else:                                 
                        tags.append ('word(t)='+m+' : 1\tiscapital : '+capital+'\tisnumber : '+number+'\thasnumber : '+h_number+'\thassplchars : '+splchars+'\thas_fc : '+has_fc+'\tparentname(t)='+parentname[0]+' : 1\tgrandparentname(t)='+parentname[1]+' : 1\tO\n') 
                        tagscount=tagscount+1
                        test.append ('word(t)='+m+' : 1\tiscapital : '+capital+'\tisnumber : '+number+'\thasnumber : '+h_number+'\thassplchars : '+splchars+'\thas_fc : '+has_fc+'\tparentname(t)='+parentname[0]+' : 1\tgrandparentname(t)='+parentname[1]+' : 1\t\n') 
                        if tagscount%5==0:
                             tags.append('\n')
                             test.append('\n')
        containertag=i
        if i.previous_sibling:
            precontainertag=i.previous_sibling
         
    linetags=[]; temp=[]; temptags=[] 
    
   
    # Cleaning out useless 'O' tags and maintaining only the ones within +/-6 tags limit for learning the transitions from 'O' to annotation value
    
    for i in range(len(tags)):
        temp=tags[i].split(' : ')
        if temp[0]=='\n':            
            pass
        else:
            temp[8]=temp[8].replace('1\t', '')
            temp[8]=temp[8].replace('\n', '')
            if temp[8] in tagset:
                temptags.append(tags[i])
            else:
                counter=0
                for j in range(10):
                    if  (i+j) <len(tags):                                              
                        temp=tags[i+j].split(' : ')
                        if not temp[0]=='\n':
                            temp[8]=temp[8].replace('1\t', '')
                            temp[8]=temp[8].replace('\n', '')
                            if temp[8] in tagset: 
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
    
    counter=0; experiment10=int((len(newtags)*0.8))
    print 'No of lines in experiment set:',  experiment10
    for i in range(len(tags)):             
        counter=counter+1
        trainfile.write(tags[i])        
        if counter%10==0:
            traindevelfile.write(tags[i])
    counter=0
    for j in range(316+experiment10): 
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
    
            
    return 1
    
    
def keywordtag(filename, tagset,  tagdict):
        starttime=time.time()
        # Reference snippet to apply return tags to the html file
        page=open(os.getcwd()+'/temp/'+filename+'.html')
        ret=open(os.getcwd()+'/temp/temp.html','w')


        soup=Soup(page)

        # The keywords that need to be tagged
        
        retfile=open(os.getcwd()+'/temp/'+filename+'.test.prediction')
        a=retfile.read().splitlines()
        tokens=[]        
        for terms in a:               
            temptoken=terms.split(' : ')  
           
            if temptoken[0]:
                temptoken[0]=temptoken[0].replace('word(t)=', '')         
                temptoken[8]=temptoken[8].replace('1\t', '')            
                if temptoken[8] in tagset:                    
                    tokens.append(temptoken) 
       
         
                
        # This chunk of code checks through the descendants for presence of NavigableStrings and replaces the string with an 'a' with title=keyword for tooltip purpose.
        w=soup

        for line in tokens:
            for child in w.descendants:
                if child.next_sibling:
                    for i in child.next_sibling:           
                        if isinstance(i,NavigableString):                           
                            if len(i)<50 and len(i)>2:     
                                reg=re.compile(line[0], re.IGNORECASE)      
                                if line[0] in i and len(line[0])>2:
                                    if i.parent.name=='a':
                                        i.parent['title']=line[8]; i.parent['style']="color:#000000; background-color:#40E0D0"
                                    else:      		  
                                        match=re.search(reg,i)
                                        start, end = match.start(), match.end()      				
                                        newtag=i[:start]+'<span style="color:#000000; background-color:#40E0D0" title="'+line[8]+'">'+line[0]+'</span>'+i[end:]				
                                        i.string.replace_with(newtag)

        
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
        




def accuracy(filename,  experiment):
    
    standardfile=open(os.getcwd()+'/temp/'+filename+'.train')
    firstfile=open(os.getcwd()+'/temp/'+filename+'.test.prediction')
    secondfile=open(os.getcwd()+'/temp/'+filename+'.'+experiment+'.test.prediction')
    predictiontracker=open(os.getcwd()+'/temp/'+filename+'.'+experiment+'.prediction.tracker', 'w')
    
    standard=standardfile.read().splitlines()
    stan=[]
    for i in standard:
        line=i.split(' : ')
        if line[0] and not line[0]=='\n':
            line=line[8].replace('1\t', '')
            line=line.replace('\n', '')
            stan.append(line)
        
    first=firstfile.read().splitlines()
    file1=[]
    for i in first:
        line=i.split(' : ')
        if line[0] and not line[0]=='\n':
            line=line[8].replace('1\t', '')
            line=line.replace('\n', '')
            file1.append(line)
        
    second=secondfile.read().splitlines()
    file2=[]
    for i in second:
        line=i.split(' : ')
        if line[0] and not line[0]=='\n':
            line=line[8].replace('1\t', '')
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
    print 'Original model accuracy is', f1
    
    f2=(b/len(stan))*100
    print 'Experimental 80% model accuracy is', f2
    
    return
    
    
    
    
    
    
    
    
    
    
    
    
    
