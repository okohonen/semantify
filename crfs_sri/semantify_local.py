#!/usr/bin/env python

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

    
def preprocess(filename):        
    

    f = open(os.getcwd()+'/temp/'+filename+'.test','w')    
    d = open(os.getcwd()+'/temp/'+filename+'.test.reference','w')
    page=open(os.getcwd()+'/temp/'+filename+'.html','r') 
    soup=Soup(page) 
    char=re.escape(string.punctuation)  
    counter=0
    tokens=[]
    alltext=soup.find_all(text=True)   
    
    
    for a in range(len(alltext)):
        alltext[a]=re.sub('[^a-zA-Z0-9\n\.\-]', ' ', alltext[a])
        #alltext[a]=re.sub(r'['+char+']', ' ',alltext[a])
        words=alltext[a].split()
        for i in range(len(words)): 
            if len(words[i])<45 and len(words[i])>0:
                tokens.append(words[i])                
               
    
    #tokens=set(tokens)   
    for i in tokens:   
        sub2=i[-2:]; sub4=i[-4:];  
        # 90:10  distribution of test and test.reference file
        counter=counter+1        
        if counter % 10 <1:
            d.write('word(t)='+i+ ' : 1 \n') 
        else:
            f.write('word(t)='+i+ ' : 1 \n')
        
                    
    f.close()   
    d.close()        
    
    return 1
    
        
def develparse(filename):   
    
    conn = sqlite3.connect('sentence.db')
    c = conn.cursor()

    
    page=open(os.getcwd()+'/temp/'+filename+'.html')
    train=open(os.getcwd()+'/temp/'+filename+'.train','w')
    devel=open(os.getcwd()+'/temp/'+filename+'.train.devel','w')    
    #develpredict=open(os.getcwd()+'/temp/'+filename+'.devel.prediction','w')    

    soup=Soup(page)
    char=re.escape(string.punctuation)

    #  Extracting the tagged texts and compiling into a list

    tagsetentity=[]; tagsetorg=[];tagsetlocation=[];tagsetdate=[];taggedtext=[]

    tagset=['entity','org','location','date']
    tagset0=soup.find_all("span", class_="WebAnnotator_entity")
    tagset1=soup.find_all("span", class_="WebAnnotator_org")
    tagset2=soup.find_all("span", class_="WebAnnotator_location")
    tagset3=soup.find_all("span", class_="WebAnnotator_date")
    compiledtag=[]

    for i in range(len(tagset0)):
        if len(tagset0[i].string)>1:
            #tagset0[i]=re.sub(r'['+char+']', '',tagset0[i].string)
            tagset0[i]=re.sub('[^a-zA-Z0-9\.\-]', ' ', tagset0[i].string)  
            tagsetentity.append(tagset0[i])
    for i in range(len(tagset1)):
        if len(tagset1[i].string)>1:
            #tagset1[i]=re.sub(r'['+char+']', '',tagset1[i].string)
            tagset1[i]=re.sub('[^a-zA-Z0-9\.\-]', ' ', tagset1[i].string)  
            tagsetorg.append(tagset1[i])
    for i in range(len(tagset2)):
        if len(tagset2[i].string)>1:
            #tagset2[i]=re.sub(r'['+char+']', '',tagset2[i].string)
            tagset2[i]=re.sub('[^a-zA-Z0-9\.\-]', ' ', tagset2[i].string)  
            tagsetlocation.append(tagset2[i])
    for i in range(len(tagset3)):
        if len(tagset3[i].string)>1:
            #tagset3[i]=re.sub(r'['+char+']', '',tagset3[i].string)
            tagset3[i]=re.sub('[^a-zA-Z0-9\.\-]', ' ', tagset3[i].string)  
            tagsetdate.append(tagset3[i])

    compiledtag=[tagsetentity,tagsetorg,tagsetlocation,tagsetdate]
    print compiledtag
    maxcount=len(compiledtag[0])+len(compiledtag[1])+len(compiledtag[2])+len(compiledtag[3])
    
    counter=0
    flag=0
    tags=[]; devels=[]

#  Checking if each string on page is tagged and assigning corresponding B,I,O tags
    print 'Adding training values to db'
    
    w=soup  
    trainingflag=0
   
    for child in w.descendants:
                if child.next_sibling:
                    for instring in child.next_sibling:				
                        if isinstance(instring,NavigableString):
                            parentname=instring.parent.name
                            if len(instring)<45 and len(instring)>0:
                                #instring=re.sub(r'['+char+']', '',instring)
                                instring=re.sub('[^a-zA-Z0-9\.-]', ' ', instring)   
                                count=0; counter=counter+1; trainingminiflag=0
                                for i in range(len(compiledtag)):
                                    for j in range(len(compiledtag[i])): 
                                        count= count+1 ; flag=1       
                                        if compiledtag[i][j] in instring and compiledtag[i][j]: 
                                            trainingflag=1
                                            instringsplit=instring.split()
                                            z=0 ;                           
                                            for m in instringsplit:                               
                                                if m in compiledtag[i][j] :                                 
                                                    ####### Code to add token to database                                
                                                    c.execute('''insert into sentences (entity, tag, added) VALUES (?,?,?)''',(m,tagset[i],  datetime.now())) 
                                                    conn.commit()    
                                                    flag=0
                                                    # collecting other features for the token
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
                                                    
                                                # counter % 10 is to reproduce 10 percent of train file as devel file
                                                    if counter % 10 <1:
                                                        #devels.append ('word(t)='+m+' : 1\tiscapital : '+capital+'\tisnumber : '+number+'\thasnumber : '+h_number+'\thassplchars : '+splchars+'\tparentname : '+parentname+'\ttagset : '+tagset[i]+'\n') 
                                                        devels.append ('word(t)='+m+' : 1\tiscapital : '+capital+'\tisnumber : '+number+'\thasnumber : '+h_number+'\thassplchars : '+splchars+'\tparentname(t)='+parentname+' : 1\ttagset : '+tagset[i]+'\n') 
                                                    else:
                                                        tags.append ('word(t)='+m+' : 1\tiscapital : '+capital+'\tisnumber : '+number+'\thasnumber : '+h_number+'\thassplchars : '+splchars+'\tparentname(t)='+parentname+' : 1\ttagset : '+tagset[i]+'\n') 
                                                else:   
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
                                                    if counter % 10 <1:
                                                        devels.append ('word(t)='+m+' : 1\tiscapital : '+capital+'\tisnumber : '+number+'\thasnumber : '+h_number+'\thassplchars : '+splchars+'\tparentname(t)='+parentname+' : 1\ttagset : O\n') 
                                                    else:
                                                        tags.append ('word(t)='+m+' : 1\tiscapital : '+capital+'\tisnumber : '+number+'\thasnumber : '+h_number+'\thassplchars : '+splchars+'\tparentname(t)'+parentname+' : 1\ttagset : O\n') 
                                        elif trainingflag==0 and trainingminiflag==0:
                                             trainingminiflag=1
                                             instringsplit=instring.split()
                                             z=0 ;                           
                                             for m in instringsplit:  
                                                    # collecting other features for the token
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
                                                    
                                                # counter % 10 is to reproduce 10 percent of train file as devel file
                                                    if counter % 10 <1:                                                       
                                                      devels.append ('word(t)='+m+' : 1\tiscapital : '+capital+'\tisnumber : '+number+'\thasnumber : '+h_number+'\thassplchars : '+splchars+'\tparentname(t)='+parentname+' : 1\ttagset : O\n') 
                                                    else:
                                                      tags.append ('word(t)='+m+' : 1\tiscapital : '+capital+'\tisnumber : '+number+'\thasnumber : '+h_number+'\thassplchars : '+splchars+'\tparentname(t)='+parentname+' : 1\ttagset : O\n') 

    print 'Added training values to db'

    #  Writing to file and closing  

    for i in range(len(tags)):
        train.write(tags[i])
    train.close()

    
    for i in range(len(devels)):
        devel.write(devels[i])        
    devel.close()
   

    print '\n\tinput file\t\t:', filename+'.html'
    print '\ttrain file\t\t:', filename+'.train'
    print '\ttrain.devel file\t:', filename+'.train.devel'
    print '\tdevel prediction file\t:', filename+'.devel.prediction'

    return 1
        
def keywordtag(filename):
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
            if temptoken[0] and temptoken[1]:
                temptoken[0]=temptoken[0].replace('word(t)=', '')            
                temptoken[1]=temptoken[1].replace('1\t', '')              
                if temptoken[2]!='O':
                    tokens.append(temptoken)   
                
        # This chunk of code checks through the descendants for presence of NavigableStrings and replaces the string with an 'a' with title=keyword for tooltip purpose.
        w=soup

        for b in tokens:           
            for child in w.descendants:
                if child.next_sibling:
                    for i in child.next_sibling:				
                        if isinstance(i,NavigableString):
                            if len(i)<50 and len(i)>2:     
                                reg=re.compile(b[0], re.IGNORECASE)      
                                if b[0] in i and len(b[0])>2:
                                    if i.parent.name=='a':
                                        i.parent['title']=b[2]; i.parent['style']="color:#000000; background-color:#40E0D0"
                                    else:      		  
                                        match=re.search(reg,i)
                                        start, end = match.start(), match.end()      				
                                        newtag=i[:start]+'<span style="color:#000000; background-color:#40E0D0" title="'+b[2]+'">'+b[0]+'</span>'+i[end:]				
                                        i.string.replace_with(newtag)
   
        # Debugging the output of test.prediction
        testfile= open(os.getcwd()+'/temp/'+filename+'.test.correction', 'w')
        for b in tokens:           
            testfile.write(b[0])
            testfile.write(':')
            testfile.write(b[2])
            testfile.write('\n')
        testfile.close()
        ###########
        
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
                line=line.replace('<html><head><body>', '')
                line=line.replace('</body></head></html>', '')
                fout.write(line)
                content.append(line)
            else:
                fout.write(line)
                content.append(line)
        fin.close()
        fout.close()
        return content


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
    if   re.match('[^a-zA-Z0-9]', token):
        return True
    else:
        return False
