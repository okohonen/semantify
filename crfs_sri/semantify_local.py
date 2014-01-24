#!/usr/bin/env python

from __future__  import division
import socket
import urllib2
import sqlite3
import os
import string
import re
import time
from bs4 import BeautifulSoup
from bs4 import NavigableString
import bs4
from datetime import datetime
import shlex, subprocess
import sys  
import zlib
from sklearn.metrics import confusion_matrix
from sklearn import cross_validation
import codecs
import devutil
import collections

# Class that implements tokenization equivalent to nltk.wordpunct_tokenize, but also returns the positions of each match
class WordPunctTokenizer:
    def __init__(self):
        self.wpre = re.compile(r'\w+|[^\w\s]+', re.UNICODE)

    def tokenize(self, s):
        return re.findall(self.wpre, s)
    
    def positioned_tokenize(self, s):
        tokens = []
        tokenstart = []
        tokenend = []
        for m in re.finditer(self.wpre, s):
            tokens.append(m.group(0))
            tokenstart.append(m.start())
            tokenend.append(m.end())
        return tokens, tokenstart, tokenend

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


def class_features(nodeparent):
    # Classname features   
    classname=''; classlong=""; classbrief= ""  
    if nodeparent.has_attr('class'): 
        classname=",".join(nodeparent['class'])
        if "WebAnnotator" in classname:          
            assert False, "WebAnnotator tags should be stripped when this is applied"
        classlong, classbrief=Ortho.generalisation(classname)             
                
    return classname, classlong,  classbrief

def htmlparse(soup):   
    nodestack = [soup.body] # Track nodes to expand
    htmlstack = [[]] # Track position in HTML-tree for feature extraction
    labelstack = ['O'] # Track labeling: All subtrees of a labeled tags have the same label
    blocknrstack = [0] # For finding "sentence" boundaries
    
    nonblocktags=['a', 'abbr', 'b', 'basefont', 'bdo', 'big', 'br', 'dfn', 'em', 'font', 'i', 'img', 'input', 'kbd', 'label', 'q', 's', 'samp', 'select', 'small', 'span', 'strike', 'strong', 'sub', 'sup', 'textarea', 'tt', 'u', 'var']
    maxblocknr = 0

    while(len(nodestack) > 0):
        node = nodestack.pop()
        stack = htmlstack.pop()
        label = labelstack.pop()
        blocknr = blocknrstack.pop()

        if isinstance(node, bs4.Tag):
            #if node.has_attr('class'):
            nodeclassname,  nodeclasslong,  nodeclassbrief=class_features(node)   
            #else:
                #nodeclassname='na';  nodeclasslong='na';  nodeclassbrief='na'
            if node!=None:
                if (node.name == "span" and "WebAnnotator" in nodeclassname):                       
                    # Find the annotation label and add to 'labels' list
                    if node.has_attr('class'):                        
                        temp=str(node).split('class')
                        temp=temp[1].split('"')
                        label=temp[1].replace('WebAnnotator_', '')
                        #devutil.keyboard()
                        
                    l = stack
                else:
                    l = [node]
                    l.extend(stack)                
                    # Node starts new block
                    if node.name not in nonblocktags:
                        maxblocknr += 1
                        blocknr = maxblocknr
                for c in reversed(node.contents):
                    nodestack.append(c)
                    htmlstack.append(l)
                    labelstack.append(label)
                    blocknrstack.append(blocknr)

        elif isinstance(node, bs4.Comment): 
            pass # Ignore comments

        elif isinstance(node, bs4.NavigableString):
            # Ignore script tags
            if node.parent.name != "script":
                yield (node, stack, label, blocknr)
        else:
            print "Unknown tag type"
            devutil.keyboard()
    
    assert(len(htmlstack) == 0)

#     return tokens, labels
 
def traverse_html_nodes(nodeiter, htmlfeaturefuns, tokenfeaturefuns, build_token_index):
    tokens = []
    labels=[]
    node_index = {}
    tok = WordPunctTokenizer()

    for node, stack, label, blocknr in nodeiter:        
        htmlf = {}
        for feat in htmlfeaturefuns:
            vd = feat.extract(stack)              
            htmlf.update(vd)                                  

        if build_token_index:
            tokenization, tokenstart, tokenend = tok.positioned_tokenize(node.string)        
            node_index[node] = (tokenstart, tokenend)
        else:
            tokenization = tok.tokenize(node.string)

        for t in tokenization:
            tokenf = {}
            for feat in tokenfeaturefuns:
                vd = feat.extract(t)
                tokenf = vd      
            labels.append(label)
            tokens.append((tokenf, htmlf, node, blocknr))
    return (tokens, labels, node_index)

class BlockFeatureFunction:
    # Feature extraction function returns a dictionary where the key is the featurename and the value
    # is a pair where the first part is the featurename-specifier and the other is the value 
    # E.g. {'word': ('remarkable', '1')} will turn into 'word(t)=remarkable : 1'
    def extract(input):
        pass

    def feature_names():
        pass


class Descendants(BlockFeatureFunction):
    def extract(self, stack):
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
        return {'parentname': (parentnames[0], '1'),  'grandparentname': (parentnames[1], '1'),  'greatgrandparentname': (parentnames[2], '1'),'classname': (classname, '1'), 'classlong': (classlong, '1'), 'classbrief': (classbrief, '1'), 'descendants': (descends, '1')}
    
    def feature_names(self):
        return ['parentname', 'grandparentname', 'greatgrandparentname','classname', 'classlong', 'classbrief', 'descendants']

class Ortho(BlockFeatureFunction):
    namemap = {'a': 'lowercase', 'A': 'capital', '1': 'number', '#': 'splchar'}

    @staticmethod
    def generalisation(token):
        # print "t: %s" % token
        alphareg=re.compile('\w', re.UNICODE)
        numreg=re.compile('[0-9]', re.UNICODE)
        long=[]
        for i in range(len(token)):
            if re.match(alphareg, token[i]):
                if re.match(numreg, token[i]):
                    long.append('1')
                elif token[i].isupper():
                    long.append('A')
                else:
                    long.append('a')
            else:
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

    @staticmethod         
    def countletters(tlong):
        counts = collections.defaultdict(int)
        for c in tlong:
            counts[c] += 1
        return counts


    def __init__(self):
        self._feature_nm = ['word', 'wordlower', 'long', 'brief']
        self._feature_nm.extend(map(lambda s: s+"count", Ortho.namemap.values()))
        self._feature_nm.extend(map(lambda s: "has" + s, Ortho.namemap.values()))

    def extract(self, token):
        tlong, tbrief = Ortho.generalisation(token);
        chartypecounts = Ortho.countletters(tlong);

        ret = {'word': (token, '1'), 'wordlower': (token.lower(), '1'), 'long': (tlong, '1') ,'brief': (tbrief, '1') }
        for k in Ortho.namemap.keys():
            ret["%scount" % Ortho.namemap[k]] = ('', str(chartypecounts[k])) 
            ret["has%s" % Ortho.namemap[k]] = ('', str(int(chartypecounts[k] > 0)))

        return ret 
    
    def feature_names(self):
        return self._feature_nm
    

def write_testfiles(path, filename, sentences):
    testfile = open(os.getcwd()+path+'/temp/'+filename+'.test','w')    
    testreferencefile = open(os.getcwd()+path+'/temp/'+filename+'.test.reference','w')    
    for i in range(len(sentences)):              
        testfile.write(sentences[i].encode('utf8'))        
        testreferencefile.write(sentences[i].encode('utf8'))
        if sentences[i] != "\n":
            testfile.write('\n')        
            testreferencefile.write('\n')
    testfile.close()
    testreferencefile.close()      

def nodeblocks(retfile, tokens, filterf):
    c = 0
    curnode = tokens[0][2]

    # Gather the nodes that have non-O tags
    curtags = []
    curfilterstat = False;

    for line in retfile:
        if line == "\n":
            continue
        if curnode != tokens[c][2]:
            if curfilterstat:
                yield (curnode, curtags)
            curtags = []
            curnode = tokens[c][2]
            curfilterstat = False;        
        parts = line.split("\t")
        tag = parts[-1].strip()
        curtags.append(tag)
        curfilterstat = curfilterstat or filterf(tag)
        c += 1
    if curfilterstat:
        yield (curnode, curtags)

    # Check that lengths match
    assert(c == len(tokens))


# Takes as input the tagged file and the tokens and then produces a list of taggings
# represented as pairs with offsets in lists of triples :[(node, [(startoffset, endoffset, tags)])]
def extract_tagged_nodes(retfile, tokens):
    ret = []

    notags = ['O', 'START', 'STOP']

    for node, tags in nodeblocks(retfile, tokens, lambda x: x not in notags):
        curtag = tags[0]
        starti = 0


        offsets = []

        for i in range(len(tags)):
            if tags[i] != curtag:
                if curtag not in notags:
                    offsets.append((starti, i-1, tags[starti]))
                starti = i
                curtag = tags[i]
        if curtag not in notags:
            offsets.append((starti, i, tags[starti]))
        ret.append((node, offsets))

    return ret

def modified_node_string(s, taggings, node_pos):
    strl = []
    lastpos = 0
    for startoffset, endoffset, tag in taggings:            
        startpos = node_pos[0][startoffset]
        endpos = node_pos[1][endoffset]
        strl.append(s[lastpos:startpos])
        strl.append('<span wa-subtypes="" wa-type="%s" class="Semantify_%s" semantify="auto">%s</span>' % (tag, tag, s[startpos:endpos]))
        lastpos = endpos
    strl.append(s[lastpos:])
    return ''.join(strl)


def apply_tagging(nodes_to_tag, node_index):
    for node, taggings in nodes_to_tag:
        devutil.keyboard()
        newnode = BeautifulSoup.NavigableString(modified_node_string(node.string, taggings, node_index[node]))
        node.string.replace_with(modified_node_string(node.string, taggings, node_index[node]))
        print str(node)

markup = '<a href="http://example.com/">I linked to <i>example.com</i></a>'
soup = BeautifulSoup(markup)
a_tag = soup.a

new_tag = soup.new_tag("b")
new_tag.string = "example.net"
a_tag.i.replace_with(new_tag)


def sentence_split(tokens):
    ltemp = []
    if len(tokens) > 0:
        curblock = tokens[0][3]
    for t in xrange(len(tokens)):        
        ltemp.append(tokens[t])
        if '.' in tokens[t][0]['word'] or (t+1 < len(tokens)  and tokens[t+1][3] != curblock):
            yield(ltemp)
            ltemp = []
            curblock = tokens[t+1][3]
    yield(ltemp)

def write_feature_line(featurenames, tokenfeat, timesuffix):
    return "\t".join(["%s%s%s%s : %s" % (f, timesuffix, '=' if len(tokenfeat[f][0]) > 0 else '', tokenfeat[f][0], tokenfeat[f][1]) for f in featurenames if tokenfeat.has_key(f)])

def window(start, end, t, sent, featurenames, featgroup):
    s = write_feature_line(featurenames, sent[t][featgroup], "(t)")
    for i in [k for k in range(start, end+1) if k!=0]:
        if i < 0:
            toffset = "%d" % i
        else:
            toffset = "+%d" % i
        timesuffix = "(t%s)" % toffset
        if t+i >= 0 and t+i < len(sent) - 1:
            s += "\t" + write_feature_line(featurenames, sent[t+i][featgroup], timesuffix)
    return s
            
def preprocess_file(page, htmlfeaturefuns=[Descendants()], tokenfeaturefuns = [Ortho()], build_node_index=False):        
    nodes = []

    nodelist = htmlparse(page)

    tokens, tags, node_index = traverse_html_nodes(nodelist, htmlfeaturefuns, tokenfeaturefuns, build_node_index)            

    words=[]; f_ortho1=[]; f_ortho3=[]; f_html=[]; labels=[]
    sentences = []

    print "Page tokens"
    print len(tokens), len(tags)
    c = 0
    sentencec = 0

    for sent in sentence_split(tokens):
        for t in range(len(sent)):
            words.append(sent[t][0]["word"])
            f_ortho1.append(write_feature_line(tokenfeaturefuns[0].feature_names(), sent[t][0], '(t)'))
            
            htmlf = write_feature_line(htmlfeaturefuns[0].feature_names(), sent[t][1], '(t)')
            f_html.append(htmlf)

            ortho3f = window(-1, 1, t, sent, tokenfeaturefuns[0].feature_names(), 0)
            f_ortho3.append(ortho3f)
            sentences.append(ortho3f + "\t" + htmlf)

            labels.append(tags[c])
            c += 1
        sentencec += 1
        words.append('\n'); f_ortho1.append('\n'); f_ortho3.append('\n'); f_html.append('\n'); labels.append('\n'); sentences.append('\n')   

    # c = 0
    # 
    # # Split sentences based on '.' and tag name not being in nonblocktags list
    # for t in xrange(len(tokens)):        
    #     if '.' in  tokens[t][0]['word(t)'] or not tokens[t][2].parent.name in nonblocktags:   
    # 
    # 
    #         if len(sentencetemp)>0:
    #             sentences.extend(sentencetemp)                              
    #             words.extend(wordstemp); f_ortho1.extend(f_ortho1temp); f_ortho3.extend(f_ortho3temp); f_html.extend(f_htmltemp); labels.extend(labeltemp)
    #             sentences.extend('\n')   
    #             words.extend('\n'); f_ortho1.extend('\n'); f_ortho3.extend('\n'); f_html.extend('\n'); labels.extend('\n')
    #             sentencetemp=[]  
    #             wordstemp=[]; f_ortho1temp=[]; f_ortho3temp=[]; f_htmltemp=[]; labeltemp=[]                  
    #             nodes.append(nodestemp)
    #             nodestemp = []
    #             c += 1
    # 
    #     previousword='na'; nextword='na'; previouslong='na'; previousbrief='a'; nextlong='na'; nextbrief='a'            
    #     if t>0:
    #         previousword=tokens[t-1][0]['word(t)']; previouslong, previousbrief= generalisation(tokens[t-1][0]['word(t)'])         
    #     if t+1<len(tokens):
    #         nextword=tokens[t+1][0]['word(t)']; nextlong, nextbrief=generalisation(tokens[t+1][0]['word(t)'])
    #     
    #     line='word(t)='+tokens[t][0]['word(t)']+' : 1\tiscapital : '+tokens[t][0]['iscapital']+'\tisnumber : '+tokens[t][0]['isnumber'] +'\thasnumber : '+tokens[t][0]['hasnumber']+'\thassplchars : '+tokens[t][0]['hassplchars']+'\t'            
    #     ortho1='long='+tokens[t][0]['long']+' : 1\tbrief='+tokens[t][0]['brief']+' : 1\t'    
    #     ortho3= 'long='+tokens[t][0]['long']+' : 1\tbrief='+tokens[t][0]['brief']+' : 1\tpreviousword='+previousword+' : 1\tpreviouslong='+previouslong+' : 1\tpreviousbrief='+previousbrief+' : 1\tnextword='+nextword+' : 1\tnextlong='+nextlong+' : 1\tnextbrief='+nextbrief+' : 1\t'
    #     html= 'parentname='+tokens[t][1]['parentname']+' : 1\tgrandparentname='+tokens[t][1]['grandparentname']+' : 1\tgreatgrandparentname='+tokens[t][1]['greatgrandparentname']+' : 1\tclassname='+tokens[t][1]['classname']+' : 1\tclasslong='+tokens[t][1]['classlong']+' : 1\tclassbrief='+tokens[t][1]['classbrief']+' : 1\tdescendants='+tokens[t][1]['descendants']+' : 1\t'
    # 
    #     sentencetemp.append(line+ortho3+html+'\n')               
    #     wordstemp.append(line); f_ortho1temp.append(ortho1); f_ortho3temp.append(ortho3); f_htmltemp.append(html); labeltemp.append(tags[t])
    #     nodestemp.append(tokens[t][2])
    # 
    # # Last sentence
    # if len(sentencetemp)>0:        
    #     sentences.extend(sentencetemp)                              
    #     words.extend(wordstemp); f_ortho1.extend(f_ortho1temp); f_ortho3.extend(f_ortho3temp); f_html.extend(f_htmltemp); labels.extend(labeltemp)

    print "Tokens after sentence split"
    print len(sentences), len(words),  len(f_ortho1),  len(f_ortho3),  len(f_html),  len(labels) 
    print len(tokens) + sentencec 
    assert(len(tokens) + sentencec == len(sentences))

    return words, f_ortho1,  f_ortho3, f_html, labels, sentences, nodes, node_index, tokens

    
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
        if temp[0]=='\n':            
            window.append('\n')
        else:
            temp[tagindex]=temp[tagindex].replace('1\t', '')            
            temp[tagindex]=temp[tagindex].replace('\n', '')
            if not temp[tagindex]=='O':               
                window.append(lines[i])
                if flag==0:
                    temp[tagindex]
                    firsttagindex=i
                    flag=1
            else:
                counter=0
                for j in range(10):
                    if  (i+j) <len(tags):                                              
                        temp=lines[i+j].split(' : ')
                        if not temp[0]=='\n':
                            temp[tagindex]=temp[tagindex].replace('1\t', '')
                            temp[tagindex]=temp[tagindex].replace('\n', '')                            
                            if not temp[tagindex]=='O': 
                                window.append(lines[i])
                                break
                            else:
                                counter=counter+1
                                if counter>8:
                                    break
                    else:
                        break
            
    
    # Writing to train file and train devel files    
    writingflag=0
    for i in range(len(lines)):
        if len(lines[i])>2:
            trainfile.write(lines[i].encode('utf-8'))
            writingflag=1
        elif writingflag==1:
            trainfile.write('\n')
            writingflag=0
 
   
    writingflag=0
    for i in range(len(window)):
        if len(window[i])>2:
            traindevelfile.write(window[i].encode('utf-8'))
            writingflag=1
        elif writingflag==1:
            traindevelfile.write('\n')
            writingflag=0
    
    trainfile.close()   
    traindevelfile.close()       
    return 1    
    
def fetch_tagnames(page, tagindex):
    tagset=[]; tagdict=[]
    for lines in page:        
        line=lines.split(' : ')      
        if len(line)>1:
            line[tagindex]=line[tagindex].replace('1\t', '')
            if not line[tagindex] in tagset and not line[tagindex]=='O':
                tagset.append(line[tagindex])
                tagdict.append('WebAnnotator_'+str(line[tagindex]))  
    return tagset,  tagdict
    
def keywordtag_htmlparse(annotations, soup, htmlfeaturefuns, tokenfeaturefuns):    

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
                
                wordtemp=[]
                newtag = ""
                for t in tk:
                    for p in range(len(annotations)): 
                        if annotations[p][0]==t and annotations[p][1]==htmlf['descendants']:       
                            wordtemp.append(annotations[p][0])
                            if  (p+1<=len(annotations)):
                                if annotations[p][1]!=annotations[p+1][1]:   
                                    wordtemp=' '.join(wordtemp)  
                                           
                                    newtag += '<span style="color:#000000; background-color:#40E0D0" wa-subtypes="" wa-type="'+annotations[p][2]+'" class="Semantify_'+annotations[p][2]+'"semantify="auto">'+wordtemp+'</span>'                 		
                                    wordtemp=[]
                                elif (p+1==len(annotations)):   
                                    wordtemp=' '.join(wordtemp)
                                    newtag += '<span style="color:#000000; background-color:#40E0D0" wa-subtypes="" wa-type="'+annotations[p][2]+'" class="Semantify_'+annotations[p][2]+'"semantify="auto">'+wordtemp+'</span>'	       
                                    wordtemp=[]
                            else:
                                break
                if len(newtag) > 0:
                    node.string.replace_with(newtag)

        else:
            print "Unknown tag type"

    
    assert(len(htmlstack) == 0)
    return 
    
def keywordtag(path, filename):

    page=open(os.getcwd()+path+filename+'.html')
    ret=open(os.getcwd()+path+'/temp/temp.html','w')

    soup=BeautifulSoup(page)

    # The keywords that need to be tagged    
    retfile=open(os.getcwd()+path+'/temp/'+filename+'.test.prediction')
    retlist=retfile.read().splitlines()
    tokens=[]
    flag=0; annovar=[];annodescendants=[]; annotag=[]
    tagset=[]; tagdict=[]    
    
    # gettting tag index first
    for lines in retlist:
        line=lines.split(' : ')
        if len(line)>1:
            tagindex=len(line)-1
            break
    print tagindex
    
    tagset,  tagdict= fetch_tagnames(retlist, tagindex)
    print tagset, tagdict
    
    
    # Obtaining annotations in the form of collocations if annotation is not a single token 
    temptag=['O',  'START', 'STOP']   
    annotations=[]
    for terms in retlist:               
        temptoken=terms.split(' : ')  
        if temptoken[0]:
            temptoken[0]=temptoken[0].replace('word(t)=', '')         
            temptoken[tagindex]=temptoken[tagindex].replace('1\t', '') 
            temptoken[tagindex-1]=temptoken[tagindex-1].replace('descendants=', '')
            temptoken[tagindex-1]=temptoken[tagindex-1].replace('1\t', '') 
            if temptoken[tagindex] in tagset and temptoken[tagindex] not in temptag:
                annotate=[temptoken[0], temptoken[tagindex-1],  temptoken[tagindex]]
                annotations.append(annotate)
    annotate=['na','na', 'na']
    annotations.append(annotate)
    
    print annotations

    # The below function calls "keywordtag_htmlparse" which is used to find the appropriate tokens and tag them provided their descendants are also the same.
    htmlfeaturefuns = [descendants]
    tokenfeaturefuns = [ortho]
    
    keywordtag_htmlparse(annotations, soup,  htmlfeaturefuns,  tokenfeaturefuns)
    
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
