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
        alltext[a]=re.sub('[^a-zA-Z\n\.]', ' ', alltext[a])
        alltext[a]=re.sub(r'['+char+']', ' ',alltext[a])
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
            tagset0[i]=re.sub(r'['+char+']', '',tagset0[i].string)
            tagset0[i]=re.sub('[^a-zA-Z0-9\.]', ' ', tagset0[i])  
            tagsetentity.append(tagset0[i])
    for i in range(len(tagset1)):
        if len(tagset1[i].string)>1:
            tagset1[i]=re.sub(r'['+char+']', '',tagset1[i].string)
            tagset1[i]=re.sub('[^a-zA-Z0-9\.]', ' ', tagset1[i])  
            tagsetorg.append(tagset1[i])
    for i in range(len(tagset2)):
        if len(tagset2[i].string)>1:
            tagset2[i]=re.sub(r'['+char+']', '',tagset2[i].string)
            tagset2[i]=re.sub('[^a-zA-Z0-9\.]', ' ', tagset2[i])  
            tagsetlocation.append(tagset2[i])
    for i in range(len(tagset3)):
        if len(tagset3[i].string)>1:
            tagset3[i]=re.sub(r'['+char+']', '',tagset3[i].string)
            tagset3[i]=re.sub('[^a-zA-Z0-9\.]', ' ', tagset3[i])  
            tagsetdate.append(tagset3[i])

    compiledtag=[tagsetentity,tagsetorg,tagsetlocation,tagsetdate]
    print compiledtag
    maxcount=len(compiledtag[0])+len(compiledtag[1])+len(compiledtag[2])+len(compiledtag[3])

    #  Extracting all the visually rendered text on page

    alltext=soup.find_all(text=True)
    alltext_length=len(alltext)
    counter=0
    flag=0
    tags=[]; devels=[]

#  Checking if each string on page is tagged and assigning corresponding B,I,O tags
    print 'Adding training values to db'
    
    
    for a in range(len(alltext)):
        if len(alltext[a])<45 and len(alltext[a])>0:
            alltext[a]=re.sub(r'['+char+']', '',alltext[a])
            alltext[a]=re.sub('[^a-zA-Z0-9\.]', ' ', alltext[a])   
            count=0; flag=0 ; counter=counter+1 
            for i in range(len(compiledtag)):
                for j in range(len(compiledtag[i])): 
                    count= count+1       
                    if compiledtag[i][j]==alltext[a] and compiledtag[i][j]: 
                        compiledtagsplit=compiledtag[i][j].split()
                        z=0 ; flag=1        
                        for m in compiledtagsplit:   
                            sub2=m[-2:] ; sub4= m[-4:];
                            if z==0:                                 
                                ####### Code to add token to database                                
                                c.execute('''insert into sentences (entity, tag, added) VALUES (?,?,?)''',(m,'B-'+tagset[i],  datetime.now()))
                                conn.commit()                                                              
                            # counter % 10 is to reproduce 10 percent of train file as devel file
                                if counter % 10 <2:
                                    devels.append ('word(t)='+m+ ' : 1\tB-'+tagset[i]+'\n') 
                                else:
                                    tags.append('word(t)='+m+ ' : 1\tB-'+tagset[i]+'\n') ; z=1
                            else:                                
                                ####### Code to add token to database                                
                                c.execute('''insert into sentences (entity, tag, added) VALUES (?,?,?)''',(m, 'I-'+tagset[i],  datetime.now()))
                                conn.commit()                                              
                                if counter % 10 <2:
                                    devels.append ('word(t)='+m+ ' : 1\tI-'+tagset[i]+'\n')
                                else:
                                    tags.append('word(t)='+m+ ' : 1\tI-'+tagset[i]+'\n')
            if count==maxcount and flag==0:   
                g=alltext[a].split()   
                for ga in g:
                        sub2=ga[-2:] ; sub4= ga[-4:];    
                        if counter % 10 <2:
                            devels.append ('word(t)='+ga+' : 1\tO\n')
                        else:
                            tags.append('word(t)='+ga+ ' : 1\tO'+'\n')        
                            

    print 'Added training values to db'
# Temp arrangement for  adding training tokens from db
    '''
    conn = sqlite3.connect('sentence.db')
    c = conn.cursor()
    counter=0   
    c.execute('select * from sentences')
    content=c.fetchall()    
    for row in content:  
        token=row[1]
        sub2=token[-2:] ; sub4= token[-4:];        
        if counter % 10 <2:
            devels.append(r'word(t)='+token+ ' : 1\tsuffix(word(t))='+sub2+' : 1\tsuffix(word(t))='+sub4+' : 1 \t'+row[2]+'\n')
        else:
            tags.append('word(t)='+token+ ' : 1\tsuffix(word(t))='+sub2+' : 1\tsuffix(word(t))='+sub4+' : 1 \t'+row[2]+'\n')
       '''
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
            temptoken[0]=temptoken[0].replace('word(t)=', '')
            if len(temptoken)>1:
                temptoken[2]=temptoken[2].replace('1\t', '')              
                if temptoken[2]!='O':
                    tokens.append(temptoken[0])   
                
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
                                        i.parent['title']=b[0]; i.parent['style']="color:#000000; background-color:#40E0D0"
                                    else:      		  
                                        match=re.search(reg,i)
                                        start, end = match.start(), match.end()      				
                                        newtag=i[:start]+'<span style="color:#000000; background-color:#40E0D0" title="'+b[0]+'">'+b[0]+'</span>'+i[end:]				
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
                line=line.replace('<html><head><body>', '')
                line=line.replace('</body></head></html>', '')
                fout.write(line)
                content.append(line)
            else:
                fout.write(line)
                content.append(line)
        fin.close()
        fout.close()

        #print 'Time elapsed is', time.time()-starttime, 'seconds'

        #print '\n\t\tInput file\t\t:', filename+'.html'
        #print '\t\tTagged file\t\t:', filename+'tagged.html'

        return content


