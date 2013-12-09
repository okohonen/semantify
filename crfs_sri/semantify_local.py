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
import bs4
from datetime import datetime
import shlex, subprocess
import sys  
import zlib
# from sklearn.metrics import confusion_matrix
# from sklearn import cross_validation
# import nltk
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
    # print "t: %s" % token
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
    if len(long) > 0:
      temp=long[0]    
      for i in range(len(long)):        
          if not temp== long[i]:
              brief.append(temp)
              temp=long[i]
      brief.append(temp)     
    long=''.join(long)
    brief=''.join(brief)
    return long, brief
    
def transactions(conn,  page_id, tokens, f_ortho1,  f_ortho3, f_html,   tags):
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

def tokenize(s):
    return s.split()
    # return nltk.wordpunct_tokenize(s)
    
def class_features(nodeparent):
    # Classname features    
    classname='na'; classlong="B"; classbrief= "A" 
    classnametemp=repr(nodeparent).split('class') 
    if len(classnametemp)>1:
        classname=classnametemp[1].split('"')
        if len(classname)>1:
            classname=classname[1] 
            if not re.search("WebAnnotator", classname):          
                classlong, classbrief=generalisation(classname) 
                
    return classname, classlong,  classbrief

def htmlparse(pagefp, htmlfeaturefuns, tokenfeaturefuns):   
    soup = Soup(pagefp)
    nodestack = [soup.body]
    htmlstack = [[]]
    labelstack = ['O']
    tokens = []
    labels=[]

    while(len(nodestack) > 0):
        node = nodestack.pop()
        stack = htmlstack.pop()
        label = labelstack.pop()

        if isinstance(node, bs4.Tag):
            nodeclassname,  nodeclasslong,  nodeclassbrief=class_features(node)   
            if node!=None:
                if (node.name == "span" and "WebAnnotator" in nodeclassname):                   
                    # Find the annotation label and add to 'labels' list
                    temp=str(node).split('class')
                    temp=temp[1].split('"')
                    label=temp[1].replace('WebAnnotator_', '')
                    l = stack
                else:
                    l = [node]
                    l.extend(stack)                
                for c in reversed(node.contents):
                    nodestack.append(c)
                    htmlstack.append(l)
                    labelstack.append(label)

        elif isinstance(node, bs4.Comment): 
            pass # Ignore comments

        elif isinstance(node, bs4.NavigableString):
            # Ignore script tags
            if node.parent.name != "script":        
                tk = tokenize(node.string)
                htmlf = {}
                for fun in htmlfeaturefuns:
                    vd = fun(stack)              
                    htmlf.update(vd)                                  
        
                ret = []
                for t in tk:
                    tokenf = {}
                    for fun in tokenfeaturefuns:
                        vd = fun(t)
                        tokenf = vd      
                    labels.append(label)
                    tokens.append((tokenf, htmlf, node.parent))
        else:
            print "Unknown tag type"
            devutil.keyboard()
    
    assert(len(htmlstack) == 0)
    return tokens, labels
    
           

def descendants(stack):
    limit=len(stack) 
    parentnames=[]    
    if limit>0 and stack[0].name:
        parentnames.append(stack[0].name)
    else:
        parentnames.append('na')
    if limit>1 and stack[1].name:
        parentnames.append(stack[1].name)
    else:
        parentnames.append('na')
    if limit >2 and stack[2].name:
        parentnames.append(stack[2].name)
    else:
        parentnames.append('na')
    # print "-".join(map(lambda x: x.name,  stack))
    classname,  classlong,  classbrief=class_features(stack[0])    
    descends="-".join(map(lambda x: x.name, stack))        
    return {'parentname': parentnames[0],  'grandparentname': parentnames[1],  'greatgrandparentname': parentnames[2],'classname': classname,'classlong': classlong, 'classbrief': classbrief, 'descendants':  descends}
    
def feature_extraction(token):
    capital=iscapital(token); number=isnumber(token); h_number=hasnumber(token) ; splchars=hassplchars(token) ;  long, brief=generalisation(token) ;    
    return capital,  number,  h_number,  splchars,  long,  brief
    
def ortho(token):
    capital,  number,  h_number,  splchars,  long,  brief= feature_extraction(token)      
    return {'word(t)': token, 'iscapital': capital,  'isnumber': number ,'hasnumber': h_number ,'hassplchars': splchars ,'long': long ,'brief': brief }
    
def preprocess_file(path,  filename):
    
    page=open(os.getcwd()+path+filename+'.html')
    
    htmlfeaturefuns = [descendants]
    
    tokenfeaturefuns = [ortho]
    
    tokens, tags = htmlparse(page, htmlfeaturefuns, tokenfeaturefuns)
    
    words=[]; f_ortho1=[]; f_ortho3=[]; f_html=[]; labels=[]
    wordstemp=[]; f_ortho1temp=[]; f_ortho3temp=[]; f_htmltemp=[]; labeltemp=[]
    sentences = []
    sentencetemp=[]   
    htmltags=['a', 'abbr', 'b', 'basefont', 'bdo', 'big', 'br', 'dfn', 'em', 'font', 'i', 'img', 'input', 'kbd', 'label', 'q', 's', 'samp', 'select', 'small', 'span', 'strike', 'strong', 'sub', 'sup', 'textarea', 'tt', 'u', 'var']
    print len(tokens), len(tags)
    
    # Split sentences based on '.' and tag name not being in htmltags list
    for t in range(len(tokens)):        
        if '.' in  tokens[t][0]['word(t)']:   
            if len(sentencetemp)>0:
                sentences.extend(sentencetemp)                              
                words.extend(wordstemp); f_ortho1.extend(f_ortho1temp); f_ortho3.extend(f_ortho3temp); f_html.extend(f_htmltemp); labels.extend(labeltemp)
                sentences.extend('\n')   
                words.extend('\n'); f_ortho1.extend('\n'); f_ortho3.extend('\n'); f_html.extend('\n'); labels.extend('\n')
                sentencetemp=[]  
                wordstemp=[]; f_ortho1temp=[]; f_ortho3temp=[]; f_htmltemp=[]; labeltemp=[]                  
        
        elif not tokens[t][2].name in htmltags: 
            
            if len(sentencetemp)>0:
                sentences.extend(sentencetemp)   
                words.extend(wordstemp); f_ortho1.extend(f_ortho1temp); f_ortho3.extend(f_ortho3temp); f_html.extend(f_htmltemp); labels.extend(labeltemp)
                sentences.extend('\n')  
                words.extend('\n'); f_ortho1.extend('\n'); f_ortho3.extend('\n'); f_html.extend('\n');labels.extend('\n')                
                sentencetemp=[]   
                wordstemp=[]; f_ortho1temp=[]; f_ortho3temp=[]; f_htmltemp=[]; labeltemp=[]
        else:
            
            previousword='na'; nextword='na'; previouslong='na'; previousbrief='a'; nextlong='na'; nextbrief='a'            
            if t>0:
                previousword=tokens[t-1][0]['word(t)']; previouslong, previousbrief= generalisation(tokens[t-1][0]['word(t)'])         
            if t+1<len(tokens):
                nextword=tokens[t+1][0]['word(t)']; nextlong, nextbrief=generalisation(tokens[t+1][0]['word(t)'])
            
            line='word(t)='+tokens[t][0]['word(t)']+' : 1\tiscapital : '+tokens[t][0]['iscapital']+'\tisnumber : '+tokens[t][0]['isnumber'] +'\thasnumber : '+tokens[t][0]['hasnumber']+'\thassplchars : '+tokens[t][0]['hassplchars']+'\t'            
            ortho1='long='+tokens[t][0]['long']+' : 1\tbrief='+tokens[t][0]['brief']+' : 1\t'    
            ortho3= 'long='+tokens[t][0]['long']+' : 1\tbrief='+tokens[t][0]['brief']+' : 1\tpreviousword='+previousword+' : 1\tpreviouslong='+previouslong+' : 1\tpreviousbrief='+previousbrief+' : 1\tnextword='+nextword+' : 1\tnextlong='+nextlong+' : 1\tnextbrief='+nextbrief+' : 1\t'
            html= 'parentname='+tokens[t][1]['parentname']+' : 1\tgrandparentname='+tokens[t][1]['grandparentname']+' : 1\tgreatgrandparentname='+tokens[t][1]['greatgrandparentname']+' : 1\tclassname='+tokens[t][1]['classname']+' : 1\tclasslong='+tokens[t][1]['classlong']+' : 1\tclassbrief='+tokens[t][1]['classbrief']+' : 1\tdescendants='+tokens[t][1]['descendants']+' : 1\t'
            
            sentencetemp.append(line+ortho3+html+'\n')               
            wordstemp.append(line); f_ortho1temp.append(ortho1); f_ortho3temp.append(ortho3); f_htmltemp.append(html); labeltemp.append(tags[t])
            
    
    
    print len(sentences), len(words),  len(f_ortho1),  len(f_ortho3),  len(f_html),  len(labels)        
    #devutil.keyboard()
    testfile = open(os.getcwd()+path+'/temp/'+filename+'.test','w')    
    testreferencefile = open(os.getcwd()+path+'/temp/'+filename+'.test.reference','w')

    for i in range(len(sentences)):              
        testfile.write(sentences[i])
        testreferencefile.write(sentences[i])
    testfile.close()
    testreferencefile.close()      
    
    return words, f_ortho1,  f_ortho3, f_html, labels

def preprocess(conn, path, filename):   

    page=open(os.getcwd()+path+filename+'.html','r')     
    testfile = open(os.getcwd()+path+'/temp/'+filename+'.test','w')    
    testreferencefile = open(os.getcwd()+path+'/temp/'+filename+'.test.reference','w') 
    soup=Soup(page)      
    counter=0
    tokens=[];    parentname=[];    tags=[];    devels=[];  test=[];    testreference=[];    
    containertag=['a','b','c'];  previousterm=['na']; ancestor=[];ancestors=[]; classnames=[]
    capital=[];number=[]; h_number=[];splchars=[];long=[]; brief=[]; classlong=[]; classbrief=[]; tagsetname=[];parentsname=[];currentterm=[]   
    htmltags=['a', 'abbr', 'b', 'basefont', 'bdo', 'big', 'br', 'dfn', 'em', 'font', 'i', 'img', 'input', 'kbd', 'label', 'q', 's', 'samp', 'select', 'small', 'span', 'strike', 'strong', 'sub', 'sup', 'textarea', 'tt', 'u', 'var']
    # Special variables used for sentence break : based on count of words that comes up inside the loop. 
    w_flag_len=[]; w_flag_count=0; flag_count=0
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
   
    reg=re.compile('WebAnnotator_[a-zA-Z0-9]')
    tokens = []
    f_ortho1 = []
    f_ortho3 = []
    f_html = []
    tags = []

    for i in soup.body.descendants:     			
        if isinstance(i,NavigableString):
            instring=re.sub('[^a-zA-Z0-9\.,\-?]', ' ', i)                            
            if len(instring)>2: 
                iterator=0;parentname=[];ancestor=[]
                for parent in i.parents:
                    iterator=iterator+1 
                    if parent.name: 
                        if parent.name=='html':
                            break
                        else:                           
                            if iterator==1 and parent.name=="span" and re.findall(reg, str(parent)):
                                continue
                            else:
                                ancestor.append(parent.name)
                                if  iterator<4:
                                    parentname.append(parent.name) 
                if len(parentname)<3:
                    for count in range(0, 4):
                        if len(parentname)<3:
                            parentname.append('na')           
                instringsplit=[]
                instringsplit.append([element for element in instring.split('.') if element]) 
                w=[p.split() for p in instringsplit[0]]                        
                if len(w[0])>0:
                    w_flag_len.append(len(w[0]))                       
                else: 
                    continue                
                for m in w[0] :                                        
                    ancestors.append('-'.join(ancestor))
                    parentsname.append(parentname)
                                      
                    # Feature extraction                    
                    capital.append(iscapital(m)); number.append(isnumber(m)) ; h_number.append(hasnumber(m)) ; splchars.append(hassplchars(m)) ;  longtemp, brieftemp=generalisation(m) ; long.append(longtemp) ;  brief.append(brieftemp); classname=re.findall('class=".*"', testcontainertag); 
                    
                    if classname and not (re.findall("WebAnnotator", str(classname))):                        
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
                    
                    if i.parent.name=='span':
                        absent=0
                        for q in range(len(tagdict)):
                            if  tagdict[q] in traincontainertag: 
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
                        #html='classname(t)='+classnames[counter-1]+' : 1\tclasslong(t)='+classlong[counter-1]+' : 1\tclassbrief(t)='+classbrief[counter-1]+' : 1\tparentname(t)='+parentsname[counter-1][0]+' : 1\tgrandparentname(t)='+parentsname[counter-1][1]+' : 1\tgreatgrandparentname(t)='+parentsname[counter-1][2]+' : 1\tancestors(t)='+ancestors[counter-1] +' : 1\t'                 
                        html='classname(t)='+classnames[counter-1]+' : 1\tclasslong(t)='+classlong[counter-1]+' : 1\tclassbrief(t)='+classbrief[counter-1]+' : 1\tparentname(t)='+parentsname[counter-1][0]+' : 1\tgrandparentname(t)='+parentsname[counter-1][1]+' : 1\t'                       
                        
                        tokens.append(line)                        
                        f_ortho1.append(ortho1)
                        f_ortho3.append(ortho3)
                        f_html.append(html)     
                        tags.append(tagsetname[counter-1])
                        test.append(line+ortho1+html+'\n')
                        w_flag_count=w_flag_count+1
                        #devutil.keyboard()  
                        
                        #print w_flag_len,  flag_count,  w_flag_count
                        if len(w_flag_len)>flag_count and w_flag_len[flag_count]==w_flag_count:
                            tokens.append('newlinesentencebreak')                        
                            f_ortho1.append('newlinesentencebreak')
                            f_ortho3.append('newlinesentencebreak')
                            f_html.append('newlinesentencebreak')     
                            tags.append('newlinesentencebreak')  
                            test.append('newlinesentencebreak')  
                            w_flag_count=0
                            flag_count=flag_count+1
                        
                        #test.append('word(t)='+currentterm[counter-1]+' : 1\tlongcurrent(t)='+longcurrent+' : 1\tbriefcurrent(t)='+briefcurrent+' : 1\tpreviousterm(t)='+previousterm[counter-1]+' : 1\tlongprevious(t)='+longprevious+' : 1\tbriefprevious(t)='+briefprevious+' : 1\tnextterm(t)='+currentterm[counter]+' : 1\tlongnext(t)='+longnext+' : 1\tbriefnext(t)='+briefnext+' : 1\tiscapital : '+capital[counter-1]+'\tisnumber : '+number[counter-1]+'\thasnumber : '+h_number[counter-1]+'\thassplchars : '+splchars[counter-1]+'\tclassname(t)='+classnames[counter-1]+' : 1\tclasslong(t)='+classlong[counter-1]+' : 1\tclassbrief(t)='+classbrief[counter-1]+' : 1\tparentname(t)='+parentsname[counter-1][0]+' : 1\tgrandparentname(t)='+parentsname[counter-1][1]+' : 1\tgreatgrandparentname(t)='+parentsname[counter-1][2]+' : 1\tancestors(t)='+ancestors[counter-1]+' : 1\t\n') 
                        
                    # previous and prepreviousterms
                    previousterm.append(m)
                    counter=counter+1
                # New line added after every sentence in test file 
                                         
        testcontainertag=i.encode('utf8')
        if "WebAnnotator" in str(testcontainertag):
            traincontainertag=(i.previous_element).encode('utf8')
        else:
            traincontainertag=i.encode('utf8')

    writingflag=0
    for i in range(len(test)):
        if not test[i]=='newlinesentencebreak':
            testfile.write(test[i])
            testreferencefile.write(test[i])
            writingflag=1
        elif writingflag==1:
            testfile.write('\n')
            testreferencefile.write('\n')
            writingflag=0
       
    testfile.close()
    testreferencefile.close() 
        
    return tokens,  f_ortho1, f_ortho3,  f_html,   tags,  tagset, tagdict
        

    
def history(conn, path, filename):    
    trainfile=open(os.getcwd()+path+'/temp/'+filename+'.train','w')
    traindevelfile=open(os.getcwd()+path+'/temp/'+filename+'.train.devel','w') 
    lines=[]
    
    c = conn.cursor()   
    # c.execute("SELECT tt.*, tags.val FROM (SELECT tokens.id AS token_id, GROUP_CONCAT(features.line, '*!*') AS f FROM tokens JOIN features ON tokens.id=features.token_id WHERE page_id=1 AND feature_set_id IN (SELECT id FROM feature_sets WHERE name IN('ortho3', 'html')) GROUP BY tokens.id) AS tt JOIN tags ON tags.token_id=tt.token_id WHERE tags.schema_id=1")
    
    schema_id = 1
    tokens = []
    tags = []
    writingflag=0
    lines=[]

    c.execute("SELECT pages.id, tokens.val, tags.val FROM pages JOIN tokens ON pages.id=tokens.page_id JOIN tags ON pages.id = tags.page_id AND pages.schema_id=tags.schema_id WHERE tags.schema_id=?", str(schema_id))    
    for values in c.fetchall():
        page_id = values[0]       
        tokens=blobdecode(str(values[1]))
        tags=blobdecode(str(values[2]))
        tokentemp=[]; tagtemp=[]; fttempa=[]; fttempb=[]
        
        c2 = conn.cursor()
        c2.execute("SELECT feature_sets.name, features.val FROM features JOIN feature_sets ON feature_set_id=feature_sets.id WHERE page_id=? AND feature_sets.name IN ('ortho3','html') ORDER BY page_id, feature_sets.id", str(page_id))

        fts = []
        for features in c2.fetchall():             
            fts.append(blobdecode(str(features[1])))   
        
    # Collecting list of lines to write to training file and devel file    
    
    tokens=tokens.split('\n'); fts[0]=fts[0].split('\n'); fts[1]=fts[1].split('\n'); tags=tags.split('\n')
    for i in range(len(tokens)):
        lines.append(tokens[i]+fts[0][i]+fts[1][i]+tags[i]+'\n')
               
       
    for i in range(len(lines)):
        if len(lines[i])>1:
            temp=lines[i].split(' : ')
            tagindex=len(temp)-1
            break
    print 'Index of label is :', tagindex
   
    # Cleaning out useless 'O' tags and maintaining only the ones within +/-10 tags limit for learning the transitions from 'O' to annotation value
    flag=0; firsttagindex=0; window=[]; 
    
    for i in range(len(lines)):
        temp=lines[i].split(' : ')           
        if len(temp)>1:   
            temp[tagindex]=temp[tagindex].replace('1\t', '')            
            if not temp[tagindex]=='O':             
                window.append(lines[i])
                if flag==0:
                    firsttagindex=i
                    flag=1
            else:
                counter=0
                for j in range(8):
                    if  (i+j) <len(lines):    
                        temp=lines[i+j]
                        if len(temp)>1:
                            temp=lines[i+j].split(' : ')                        
                            temp[tagindex]=temp[tagindex].replace('1\t', '')                            
                            if not temp[tagindex]=='O': 
                                window.append(lines[i])                               
                                break
                            else:
                                counter+=1
                                if counter>7:
                                    break 
                        else:
                            counter+=1                
                            window.append('\n')
                    else:
                        break
        else:
            window.append('\n')
    
    # Writing to train file and train devel files    
    writingflag=0
    for i in range(len(lines)):
        if len(lines[i])>2:
            trainfile.write(lines[i])
            writingflag=1
        elif writingflag==1:
            trainfile.write('\n')
            writingflag=0
 
   
    writingflag=0
    for i in range(len(window)):
        if len(window[i])>2:
            trainfile.write(window[i])
            writingflag=1
        elif writingflag==1:
            trainfile.write('\n')
            writingflag=0
    
    trainfile.close()   
    traindevelfile.close()       
    return 1    
    
def fetch_tagnames(page, tagindex):
    for lines in page:        
        line=lines.split(' : ')      
        if len(line)>1:
            line[tagindex]=line[tagindex].replace('1\t', '')
            if not line[tagindex] in tagset and not line[tagindex] in temptag:
                tagset.append(line[tagindex])
                tagdict.append('WebAnnotator_'+str(line[tagindex]))  
    return tagset,  tagdict
    
def keywordtag(path, filename):
 
    # Reference snippet to apply return tags to the html file
    page=open(os.getcwd()+path+filename+'.html')
    ret=open(os.getcwd()+path+'/temp/temp.html','w')

    soup=Soup(page)

    # The keywords that need to be tagged    
    retfile=open(os.getcwd()+path+'/temp/'+filename+'.test.prediction')
    retlist=retfile.read().splitlines()
    tokens=[]
    flag=0; temptag=['O',  'START', 'STOP'];annovar=[];annotations=[]
    tagset=[]; tagdict=[]    
    
    # gettting tag index first
    for lines in retlist:
        line=lines.split(' : ')
        if len(line)>1:
            tagindex=len(line)-1
            break
    print tagindex
    
    tagset,  tagdict= fetch_tagnames(retlist, tagindex)
    
    
    # Obtaining annotations in the form of collocations if annotation is not a single token    
    for terms in retlist:               
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
    w=soup.body

    for line in annotations:
        for child in w.descendants:
            if child.next_sibling:
                for i in child.next_sibling:           
                    if isinstance(i,NavigableString): 
                        if len(i)<1000 and len(i)>0:   
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
