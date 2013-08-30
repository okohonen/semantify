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


def develparse(filename):   
    
    conn = sqlite3.connect('sentence.db')
    c = conn.cursor()

    
    page=open(os.getcwd()+'/temp/'+filename+'.html')
    train=open(os.getcwd()+'/temp/'+filename+'.train','w')
    devel=open(os.getcwd()+'/temp/'+filename+'.train.devel','w')    

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
        if len(alltext[a])<45 and len(alltext[a])>2:
            alltext[a]=re.sub(r'['+char+']', '',alltext[a])
            alltext[a]=re.sub('[^a-zA-Z0-9\.]', ' ', alltext[a])   
            count=0; flag=0 ; counter=counter+1 
            for i in range(len(compiledtag)):
                for j in range(len(compiledtag[i])): 
                    count= count+1       
                    if compiledtag[i][j]==alltext[a]: 
                        compiledtagsplit=compiledtag[i][j].split()
                        z=0 ; flag=1        
                        for m in compiledtagsplit:   
                            sub2=m[-2:] ; sub4= m[-4:];
                            if z==0: 
                                tags.append('word(t)='+m+ ' : 1\tsuffix(word(t))='+sub2+' : 1\tsuffix(word(t))='+sub4+' : 1 \tB-'+tagset[i]+'\n') ; z=1
                                ####### Code to add token to database                                
                                c.execute('''insert into samples (content, added) VALUES (?,?)''',(m,'B-'+tagset[i],  datetime.now()))
                                conn.commit()
                                devels.append ('word(t)='+m+ ' : 1\tsuffix(word(t))='+sub2+' : 1\tsuffix(word(t))='+sub4+' : 1 \tB-'+tagset[i]+'\n')  
                            # counter % 10 is to reproduce 10 percent of train file as devel file
                                #if counter % 10 <=5:
                                    #devels.append ('word(t)='+m+ ' : 1\tsuffix(word(t))='+sub2+' : 1\tsuffix(word(t))='+sub4+' : 1 \tB-'+tagset[i]+'\n')               
                            else:
                                tags.append('word(t)='+m+ ' : 1\tsuffix(word(t))='+sub2+' : 1\tsuffix(word(t))='+sub4+' : 1 \tI-'+tagset[i]+'\n')
                                ####### Code to add token to database
                                tagset[i]
                                c.execute('''insert into samples (content, added) VALUES (?,?)''',(m, 'I-'+tagset[i],  datetime.now()))
                                conn.commit()
                                devels.append ('word(t)='+m+ ' : 1\tsuffix(word(t))='+sub2+' : 1\tsuffix(word(t))='+sub4+' : 1 \tI-'+tagset[i]+'\n')
                                #if counter % 10 <=5:
                                    #devels.append ('word(t)='+m+ ' : 1\tsuffix(word(t))='+sub2+' : 1\tsuffix(word(t))='+sub4+' : 1 \tI-'+tagset[i]+'\n')
            if count==maxcount and flag==0:   
                g=alltext[a].split()   
                for ga in g:
                        sub2=ga[-2:] ; sub4= ga[-4:];
                        tags.append('word(t)='+ga+ ' : 1\tsuffix(word(t))='+sub2+' : 1\tsuffix(word(t))='+sub4+' : 1 \tO'+'\n')
                        devels.append ('word(t)='+ga+ ' : 1\tsuffix(word(t))='+sub2+' : 1\tsuffix(word(t))='+sub4+' : 1 \tO\n')
                        #tags.append(ga+'\n')
                        #if counter % 10 <1:
                            #devels.append ('word(t)='+ga+ ' : 1\tsuffix(word(t))='+sub2+' : 1\tsuffix(word(t))='+sub4+' : 1 \tO\n')
                            #devels.append (ga+'\n')

    print 'Added training values to db'
# Temp arrangement for  adding training tokens from db

    conn = sqlite3.connect('sample.db')
    c = conn.cursor()
    counter=0   
    c.execute('select * from samples')
    content=c.fetchall()    
    for row in content:  
        token=row[1]
        sub2=token[-2:] ; sub4= token[-4:];
        tags.append('word(t)='+token+ ' : 1\tsuffix(word(t))='+sub2+' : 1\tsuffix(word(t))='+sub4+' : 1 \t'+row[2]+'\n')
        devels.append('word(t)='+token+ ' : 1\tsuffix(word(t))='+sub2+' : 1\tsuffix(word(t))='+sub4+' : 1 \t'+row[2]+'\n')
        #if counter % 10 <=5:
            #devels.append(row[1]+'\n')
        
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

    return 1
