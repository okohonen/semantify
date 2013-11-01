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
import zlib
from sklearn.metrics import confusion_matrix
import devutil

# Convert to utf-8 so zlib doesn't get confused
def blobencode(s):
    return zlib.compress(s.encode('utf8'))

def blobdecode(s):
    return zlib.decompress(s).decode('utf8')

def insert_new_page(cursor, o, version, schema_id = 1):
    cursor.execute('''INSERT INTO pages (url, body, timestamp, version, schema_id) VALUES (?, ?, DATETIME('now'), ?, ?)''', (o['url'], sqlite3.Binary(blobencode(o['content'])), version, schema_id))
    return cursor.lastrowid

def update_page(cursor, page_id, o):
    cursor.execute('''UPDATE pages SET url=?, body=?, timestamp=DATETIME('now') WHERE id=? ''', (o['url'], sqlite3.Binary(blobencode(o['content'])), page_id))
        

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
    
def transactions(conn, path, page_id, tokens,  f_ortho1, f_ortho3,  f_html,   tags):
    c=conn.cursor()
    schema_id = 1
    # Running through all lines in page: tokenizing, adding to db
    c.execute('BEGIN TRANSACTION')
    c.execute('DELETE FROM tokens WHERE page_id=?',  str(page_id))
    c.execute('DELETE FROM features WHERE page_id=?',  str(page_id))
    c.execute('DELETE FROM tags WHERE page_id=? AND schema_id=?',  (str(page_id), str(schema_id)))
    
    c.execute("INSERT INTO tokens (page_id, val) VALUES (?, ?)",  (page_id, sqlite3.Binary(blobencode("\n".join(tokens)))))    
    c.execute("INSERT INTO features (page_id, feature_set_id, val) VALUES (?, (SELECT id FROM feature_sets WHERE name='ortho1'),?)",  (page_id, sqlite3.Binary(blobencode('\n'.join(f_ortho1)))))
    c.execute("INSERT INTO features (page_id, feature_set_id, val) VALUES (?, (SELECT id FROM feature_sets WHERE name='ortho3'),?)",  (page_id, sqlite3.Binary(blobencode('\n'.join(f_ortho3)))))
    c.execute("INSERT INTO features (page_id, feature_set_id, val) VALUES (?, (SELECT id FROM feature_sets WHERE name='html'),?)",  (page_id,sqlite3.Binary(blobencode('\n'.join(f_html)))))    
    c.execute("INSERT INTO tags (page_id, schema_id, val) VALUES (?, ?, ?)",  (page_id, schema_id, sqlite3.Binary(blobencode('\n'.join(tags)))))
 
    conn.commit()
    return
    
def preprocess(conn, path, filename, tagindex, page_id):   

    page=open(os.getcwd()+path+filename+'.html','r')     
    testfile = open(os.getcwd()+path+'/temp/'+filename+'.test','w')    
    testreferencefile = open(os.getcwd()+path+'/temp/'+filename+'.test.reference','w') 
    soup=Soup(page)    
    counter=0
    tokens=[];    parentname=[];    tags=[];    devels=[];  test=[];    testreference=[];    
    containertag=['a','b','c'];  previousterm=['na']; ancestor=[];ancestors=[]; classnames=[]
    capital=[];number=[]; h_number=[];splchars=[];long=[]; brief=[]; classlong=[]; classbrief=[]; tagsetname=[];parentsname=[];currentterm=[]   
    
   
    # Extracting the tagset names from page
    reg=re.compile('WebAnnotator_[a-zA-Z0-9]')
    tagdict=[]; tagset=[]
    taglist= soup.find_all('span', class_=reg)
    for index in taglist:
        index=str(index).split('"')
        if not index[1] in tagdict:
            tagdict.append(index[1])
            tagtemp=index[1].replace('WebAnnotator_', '')
            tagset.append(tagtemp)
    if not tagdict:
        tagdict=['O']
        tagset=['O']
    
    print tagdict,  tagset
   
    
    tokens = []
    f_ortho1 = []
    f_ortho3 = []
    f_html = []
    tags = []

    for i in soup.body.descendants:     			
        if isinstance(i,NavigableString):    
            instring=re.sub('[^a-zA-Z0-9\.,\-?]', ' ', i)              
            if len(instring)<50 and len(instring)>1: 
                iterator=0;parentname=[];ancestor=[]
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
                    ancestors.append('-'.join(ancestor))
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
                        
                    # #######           
                    currentterm.append(m)                    
                    
                    if parentname[0]=='span':
                        absent=0
                        for q in range(len(tagdict)):
                            if  tagdict[q] in containertag: 
                                 tagsetname.append(tagset[q])
                                 absent=0
                                 break
                            else:
                                absent=1
                        if absent==1:
                            tagsetname.append('O')
                    else:                                 
                        tagsetname.append('O')                    
                    

                    if counter>1:   
                        longprevious, briefprevious=generalisation(previousterm[counter-1])                                             
                        longcurrent, briefcurrent=generalisation(currentterm[counter-1])                  
                        longnext, briefnext=generalisation(currentterm[counter])     
                        
                        # Insert into  the features with corresponding features_set_id 
                        line = 'word(t)='+currentterm[counter-1]+' : 1\tiscapital : '+capital[counter-1]+'\tisnumber : '+number[counter-1]+'\thasnumber : '+h_number[counter-1]+'\thassplchars : '+splchars[counter-1]+'\t'
                        ortho1='longcurrent(t)='+long[counter-1]+' : 1\tbriefcurrent(t)='+ brief[counter-1]+' : 1\t'
                        ortho3='longcurrent(t)='+longcurrent+' : 1\tbriefcurrent(t)='+briefcurrent+' : 1\tpreviousterm(t)='+previousterm[counter-1]+' : 1\tlongprevious(t)='+longprevious+' : 1\tbriefprevious(t)='+briefprevious+' : 1\tnextterm(t)='+currentterm[counter]+' : 1\tlongnext(t)='+longnext+' : 1\tbriefnext(t)='+briefnext+' : 1\t'
                        html='classname(t)='+classnames[counter-1]+' : 1\tclasslong(t)='+classlong[counter-1]+' : 1\tclassbrief(t)='+classbrief[counter-1]+' : 1\tparentname(t)='+parentsname[counter-1][0]+' : 1\tgrandparentname(t)='+parentsname[counter-1][1]+' : 1\tgreatgrandparentname(t)='+parentsname[counter-1][2]+' : 1\tancestors(t)='+ancestors[counter-1] +' : 1\t'                 
                        # # Srikrishna edit: instead of append(currenterm[counter-1], append(line)
                        tokens.append(line)                        
                        f_ortho1.append(ortho1)
                        f_ortho3.append(ortho3)
                        f_html.append(html)     
                        tags.append(tagsetname[counter-1])
                        
                        test.append('word(t)='+currentterm[counter-1]+' : 1\tlongcurrent(t)='+longcurrent+' : 1\tbriefcurrent(t)='+briefcurrent+' : 1\tpreviousterm(t)='+previousterm[counter-1]+' : 1\tlongprevious(t)='+longprevious+' : 1\tbriefprevious(t)='+briefprevious+' : 1\tnextterm(t)='+currentterm[counter]+' : 1\tlongnext(t)='+longnext+' : 1\tbriefnext(t)='+briefnext+' : 1\tiscapital : '+capital[counter-1]+'\tisnumber : '+number[counter-1]+'\thasnumber : '+h_number[counter-1]+'\thassplchars : '+splchars[counter-1]+'\tclassname(t)='+classnames[counter-1]+' : 1\tclasslong(t)='+classlong[counter-1]+' : 1\tclassbrief(t)='+classbrief[counter-1]+' : 1\tparentname(t)='+parentsname[counter-1][0]+' : 1\tgrandparentname(t)='+parentsname[counter-1][1]+' : 1\tgreatgrandparentname(t)='+parentsname[counter-1][2]+' : 1\tancestors(t)='+ancestors[counter-1]+' : 1\t\n') 
                        test.append('\n')
                    # previous and prepreviousterms
                    previousterm.append(m)
                    counter=counter+1
        containertag=i.encode('utf8')    
        
    
    
    for i in range(len(test)):        
        testfile.write(test[i])
        if i>1 and i%10==0:
            if len(test[i])>1:
                testreferencefile.write(test[i])
                testreferencefile.write('\n')
    testfile.close()
    testreferencefile.close() 
        
    return tokens,  f_ortho1, f_ortho3,  f_html,   tags
        

    
def history(conn, path, filename):    
    trainfile=open(os.getcwd()+path+'/temp/'+filename+'.train','w')
    traindevelfile=open(os.getcwd()+path+'/temp/'+filename+'.train.devel','w') 
    lines=[]
    c = conn.cursor()   
    # c.execute("SELECT tt.*, tags.val FROM (SELECT tokens.id AS token_id, GROUP_CONCAT(features.line, '*!*') AS f FROM tokens JOIN features ON tokens.id=features.token_id WHERE page_id=1 AND feature_set_id IN (SELECT id FROM feature_sets WHERE name IN('ortho3', 'html')) GROUP BY tokens.id) AS tt JOIN tags ON tags.token_id=tt.token_id WHERE tags.schema_id=1")
    
    schema_id = 1
    c.execute("SELECT pages.id, tokens.val, tags.val FROM pages JOIN tokens ON pages.id=tokens.page_id JOIN tags ON pages.id = tags.page_id AND pages.schema_id=tags.schema_id WHERE tags.schema_id=?", str(schema_id))    
    for values in c.fetchall():
        page_id = values[0]
        tokens = blobdecode(str(values[1]))
        tags = blobdecode(str(values[2]))
        
        c2 = conn.cursor()
        c2.execute("SELECT feature_sets.name, features.val FROM features JOIN feature_sets ON feature_set_id=feature_sets.id WHERE page_id=? AND feature_sets.name IN ('ortho3', 'html') ORDER BY page_id, feature_sets.id", str(page_id))

        fts = []
        for features in c2.fetchall():
            fts.append(blobdecode(str(features[1])))

        # Continue here and load the features by the same principles
        #print "Check the variables body, tags and fts and join them to a training file"
        #devutil.keyboard()
 
    tokentemp=[token for token in str(tokens).strip().split('\n')]
    tagtemp=[token for token in str(tags).strip().split('\n')]
    fttempa=[token for token in str(fts [0]).strip().split('\n')]    
    fttempb=[token for token in str(fts [1]).strip().split('\n')]
    print len(tokentemp),  len(tagtemp), len(fttempb)  
    
    for i in range(len(tokentemp)-1):       
        lines.append(tokentemp[i]+fttempa[i]+fttempb[i]+tagtemp[i]+'\n')  


    # Writing to train, train devel, test, test devel files
    for i in range(len(lines)):        
        trainfile.write(lines[i])
        trainfile.write('\n')
        if i>1 and i%10==0:
            if len(lines[i])>1:
                traindevelfile.write(lines[i])
                traindevelfile.write('\n')
    trainfile.close()   
    traindevelfile.close()   
    
    return 1
    
    
def keywordtag(path, filename, tagdict, tagset, tagindex):
 
    # Reference snippet to apply return tags to the html file
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
            
    # This chunk of code checks through the descendants for presence of NavigableStrings and replaces the string with an 'a' with title=category_value for tooltip purpose.
    w=soup

    for line in annotations:
        for child in w.descendants:
            if child.next_sibling:
                for i in child.next_sibling:           
                    if isinstance(i,NavigableString): 
                        if len(i)<100 and len(i)>0:   
                            if line[0] in i and len(line[0])>1:                                    
                                if i.parent.name=='a':
                                    i.parent['title']=line[1]; i.parent['style']="color:#000000; background-color:#40E0D0"                            
                                #elif i.parent.name=='span' and [k in containertag for k in tagdict]:                                        
                                    #continue
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

    fin = open(os.getcwd()+path+'/temp/temp.html')
    fout = open(os.getcwd()+path+'/temp/'+filename+'tagged.html', 'w')
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
    

def accuracy(path, filename, tagindex):
    
    standardfile=open(os.getcwd()+path+'/temp/'+filename+'.train')
    firstfile=open(os.getcwd()+path+'/temp/'+filename+'.test.prediction')
    predictiontracker=open(os.getcwd()+path+'/temp/'+filename+'.prediction.tracker', 'w')
    
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
 
    a=0; b=0
    for i in range(len(stan)):
        if stan[i]==file1[i]:
            a=a+1
        predictiontracker.write(stan[i]); predictiontracker.write('\t')
        predictiontracker.write(file1[i]); predictiontracker.write('\t')
        predictiontracker.write('\n')
    predictiontracker.close()
            
    
    f1=(a/len(stan))*100
    print 'Original model accuracy is : ', f1
    
    return
        
def confusionmatrix(path, filename, confusion,  tagset):

    predictionfile=open(os.getcwd()+path+'/temp/'+filename+'.prediction.tracker')
    
    confusionfile=open(os.getcwd()+path+'/temp/'+filename+'.'+confusion+'.confusion', 'w')    
    
    
    prediction=predictionfile.read().splitlines()
    true=[]; predfull=[]
    pred=[]
    
    def replace(token):
        absent=0; order=[0]
        for q in range(len(tagset)):
            if  tagset[q] in token:  
                token=q+1
                if not (q+1) in order:
                    order.append(q+1)
                absent=0
                break
            else:
                absent=1
        if absent==1:
            token=0
        return token
    
    order=[0]
    for i in range(len(prediction)):
        line=prediction[i].split('\t')   
        line[0]=replace(line[0])
        if not line[0] in order:
            order.append(line[0])
        line[1]=replace(line[1])
        true.append(line[0])
        predfull.append(line[1])
        confusionfile.write(repr(line))
        confusionfile.write('\n')       
    
    confusionfile.close()        
    
    if not len(order)==len(tagset)+1:
        for i in range(len(tagset)+1):
            if not i in order:
                true.append(i)
                predfull.append(i)
                pred.append(i)
               
    print  'Confusion matrix for Original model is :', confusion_matrix( predfull,  true)

    return confusion_matrix(predfull,  true)
