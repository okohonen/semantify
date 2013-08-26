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



def receive_file(filename):
    host = 'localhost'
    port = 50001
    size = 4096
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host,port))    

    #sock.send(filename)	
    f=open (os.getcwd()+"/"+filename+".html", 'r') 
    sock.send('SEND')
    l=f.read().split('\n')		
    for line in range(len(l)):
        if line <len(l)-1:
            if l[line]:
                sock.send(l[line])
                data=sock.recv(size)
                if data=='200':
                    continue
                elif data==404:
                    print 'Unexpected error while transporting file'					
        else:				
            f.close()		
            sock.send('FileOver')
            data=sock.recv(size)
            if data==404:
                break	

    sock.send('Completed')
    #print 'Sending completed'
    sock.close()
    return 1

    
def preprocess(filename):        
    

    f = open(os.getcwd()+'/temp/'+filename+'.test','w')
    d = open(os.getcwd()+'/temp/'+filename+'.test.devel','w')
    filename=open(os.getcwd()+'/temp/'+filename+'.html','r') 
    soup=Soup(filename) 
    char=re.escape(string.punctuation)  
    counter=0
    tokens=[]
    alltext=soup.find_all(text=True)   
    
    
    for a in range(len(alltext)):
        alltext[a]=re.sub('[^a-zA-Z\n\.]', ' ', alltext[a])
        alltext[a]=re.sub(r'['+char+']', ' ',alltext[a])
        words=alltext[a].split()
        for i in range(len(words)): 
            if len(words[i])<45 and len(words[i])>2:
                tokens.append(words[i])                
               
    
    tokens=set(tokens)   
    for i in tokens:   
        f.write(i+'\n')
        counter=counter+1        
        if counter % 10 <1:
            d.write(i+'\n') 
        
                    
    f.close()
    d.close()    
    
    #print '\n\tinput file\t\t:' ,filename+'.html'
    #print '\ttest file\t\t:' ,filename+'.test'
    #print '\ttest.devel file\t\t:', filename+'.test.devel'
    
    return 1
        
def develparse(filename):   
    
    conn = sqlite3.connect('sample.db')
    c = conn.cursor()
    #c.execute('''CREATE TABLE IF NOT EXISTS samples (id INTEGER PRIMARY KEY AUTOINCREMENT, content text, added datetime)''')
    
    page=open(os.getcwd()+'/temp/'+filename+'.html')
    train=open(os.getcwd()+'/temp/'+filename+'.train','w')
    devel=open(os.getcwd()+'/temp/'+filename+'.train.devel','w')    

    soup=Soup(page)
    char=re.escape(string.punctuation)

    #  Extracting the tagged texts and compiling into a list

    tagsetentity=[]; tagsetorg=[];tagsetlocation=[];tagsetdate=[];taggedtext=[]

    tagset=['prefix','stem','suffix','lemma']
    tagset0=soup.find_all("span", class_="WebAnnotator_prefix")
    tagset1=soup.find_all("span", class_="WebAnnotator_stem")
    tagset2=soup.find_all("span", class_="WebAnnotator_suffix")
    tagset3=soup.find_all("span", class_="WebAnnotator_lemma")
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
                            if z==0:        
                                tags.append(m+ '\tB-'+tagset[i]+'\n') ; z=1
                                ####### Code to add token to database
                                k=tagset[i]
                                c.execute('''insert into samples (content, added) VALUES (?,?)''',(m, datetime.now()))
                                conn.commit()
                            # counter % 10 is to reproduce 10 percent of train file as devel file
                                if counter % 10 <=5:
                                    devels.append (m+ '\tB-'+tagset[i]+'\n')               
                            else:
                                tags.append(m+ '\tI-'+tagset[i]+'\n')
                                ####### Code to add token to database
                                tagset[i]
                                c.execute('''insert into samples (content, added) VALUES (?,?)''',(m, datetime.now()))
                                conn.commit()
                                if counter % 10 <=5:
                                    devels.append (m+ '\tI-'+tagset[i]+'\n')
            if count==maxcount and flag==0:   
                g=alltext[a].split()   
                for ga in g:
                        #tags.append(ga+'\tO'+'\n')
                        tags.append(ga+'\n')
                        if counter % 10 <1:
                            #devels.append (ga+'\tO'+'\n')
                            devels.append (ga+'\n')

    print 'Added training values to db'
# Temp arrangement for  adding training tokens from db

    conn = sqlite3.connect('sample.db')
    c = conn.cursor()
    counter=0   
    c.execute('select * from samples')
    content=c.fetchall()    
    for row in content:       
        tags.append(row[1]+'\n')
        if counter % 10 <=5:
            devels.append(row[1]+'\n')
        
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
        
def keywordtag(filename):
        starttime=time.time()
        # Reference snippet to apply return tags to the html file
        page=open(os.getcwd()+'/temp/'+filename+'.html')
        ret=open(os.getcwd()+'/temp/temp.html','w')


        soup=Soup(page)

        # The keywords that need to be tagged

        retfile=open(os.getcwd()+'/temp/'+filename+'.segmentation')
        a=retfile.read().splitlines()
        tokens=[]
        for terms in a:
            temptoken=terms.split('\t')
            if not temptoken[0]==temptoken[1]:
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
                                        i.parent['title']=b[1]; i.parent['style']="color:#000000; background-color:#40E0D0"
                                    else:      		  
                                        match=re.search(reg,i)
                                        start, end = match.start(), match.end()      				
                                        newtag=i[:start]+'<span style="color:#000000; background-color:#40E0D0" title="'+b[1]+'">'+b[0]+'</span>'+i[end:]				
                                        i.string.replace_with(newtag)
   
   

        for i in soup:		
            ret.write(repr(i))
            
        lt='&lt;' ; gt='&gt;'

        page.close()
        ret.close()

        # Since Beautifulsoup uses unicode, work around here is opening the temp file and replacing the tags with appropriate '<','>' and saving the file.

        fin = open(os.getcwd()+'/temp/temp.html')
        fout = open(os.getcwd()+'/temp/'+filename+'tagged.html', 'w')
        for line in fin:
            if lt in line or gt in line:
                line=line.replace('&lt;','<')    
                line=line.replace('&gt;','>')
                fout.write(line)
            else:
                fout.write(line)
        fin.close()
        fout.close()

        #print 'Time elapsed is', time.time()-starttime, 'seconds'

        #print '\n\t\tInput file\t\t:', filename+'.html'
        #print '\t\tTagged file\t\t:', filename+'tagged.html'

        return 1

        
def send_file( filename):
        host = 'localhost'
        port = 50001
        size = 4096
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host,port))
        size=4096   
        
        #sock.send(filename)
        f=open(os.getcwd()+"/temp/"+filename+".html", 'w')
        sock.send('RECV')

        data=sock.recv(size)
        if data:
    
            while not data=='FileOver':						
                f.write(data)
                sock.send('200')												
                data=sock.recv(size)	
    
            f.close()
            sock.send('404')					
            data=sock.recv(size)
            #print data
            if data=='Completed':	
                sock.close()
        #print 'Receving completed'					
    
        return 1
        
        
def backend(filename):
    
    #   Opening error log 
    errorlog=open(os.getcwd()+'/temp/errorlog.txt',  'wb')
    successlog=open(os.getcwd()+'/temp/successlog.txt',  'wb')

    # Garbage collection in database
    GC=1
    
    try:
     
        #filename='snippetfile'
        
        #filename              =os.getcwd()+'/'+filename+'.html'
        trainfile               =os.getcwd()+'/temp/'+filename+'.train'    
        traindevelfile       =os.getcwd()+'/temp/'+filename+'.train.devel'
        testfile                 =os.getcwd()+'/temp/'+filename+'.test'
        testdevelfile         =os.getcwd()+'/temp/'+filename+'.test.devel'
        segmentationfile =os.getcwd()+'/temp/'+filename+'.segmentation' 
        clientmodel         =os.getcwd()+'/temp/'+filename+'.model'
        standardmodel          =os.getcwd()+'/morphochal2010+eng.model'        
        
        value=0
        value=semantify.preprocess(filename)
        if value==1:
            value=0
            value=semantify.develparse(filename)
            if value==1:
                command='python train.py --train_file %s --devel_file %s --prediction_file %s --model_file %s --verbose' % (trainfile,traindevelfile, segmentationfile, clientmodel)
                args = shlex.split(command)
                process=subprocess.Popen(args)
                process.wait() 
                command='python apply.py --model_file %s --test_file %s --prediction_file %s --verbose' % (standardmodel,testfile, segmentationfile)
                args = shlex.split(command)
                process=subprocess.Popen(args)
                process.wait()
                value=0
                value=semantify.keywordtag(filename)
                
        successlog.write(filename)
        successlog.write('\t')
        successlog.write( str(datetime.now()))
        successlog.write('\n')    
        print 'Processing Complete for filename', filename, str(datetime.now())   
        
    except Exception as e:
        errorlog.write(filename)
        errorlog.write('\t')
        errorlog.write(str(datetime.now()))
        errorlog.write('\t')
        errorlog.write(str(e))       
        errorlog.write('\n')
        raise e        
  
    finally:
        pass
        
    return 1

        
########## Garbage collection in database  #########
        
def garbagecollection():
    
    conn = sqlite3.connect('sample.db')
    c = conn.cursor()
    
    c.execute('select * from samples')
    content=c.fetchall()
    tokens=[]
    print len(content)
    for row in content:   
        tokens.append(row[1])
          
    tokens=set(tokens)      
    print len(tokens)
    
    c.execute('delete from samples')
    
    for i in tokens:
        c.execute('''insert into samples (content, added) VALUES (?,?)''',(i, datetime.now()))        
    return 1

            
