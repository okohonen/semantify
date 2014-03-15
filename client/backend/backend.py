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

from crfs import *
import sys  
from sklearn import metrics
from sklearn.metrics import confusion_matrix
from sklearn import cross_validation
import codecs
import devutil
import collections
import gzip
import math

def log(s):
    sys.stderr.write(s)


class Backend:    
    conn = None
    c = None
    models = []

    def __init__(self):
        # Work from directory of the current file
        self.localdir = os.path.dirname(os.path.abspath(__file__))

        dbname = "semantify.db"
        inifile = "%s/semantify.ini" % self.localdir
        if os.path.exists(inifile):
            dt = open(inifile, "r").readlines()
            dbname = dt[0].strip()
            
        dbfile = "%s/data/index/%s.db" % (self.localdir, dbname)
        log("Database file set to %s\n" % dbfile)

        if not os.path.exists(dbfile):
            os.system("sqlite3 %s < %s/schema.sql" % (self.localdir, dbfile))

        self.conn = sqlite3.connect(dbfile)
        self.c = self.conn.cursor()
        self.c.execute("PRAGMA foreign_keys = ON;")
        self.fetch_models()

    def fetch_models(self):
        names = self.c.execute("SELECT name FROM models;")
        for row in names:
            self.models.append(row[0])

    def get_models(self):
        return self.models

    def add_model(self, model_name):        
        self.c.execute("INSERT INTO models (name) VALUES (?)", (model_name, ))
        self.models.append(model_name)

    def get_page_annotated_version(self, url):
        self.c.execute('''SELECT MAX(version) FROM pages_annotated WHERE url=?''', (url,))
        r = self.c.fetchone()
        return r[0]

    def page_annotated_filename(self, model_name, page_id, is_body):
        suffix = "htmlbody" if is_body else "html"
        return "%s/data/index/%s_%s.%s.gz" % (self.localdir, model_name, page_id, suffix)
    
    def page_feature_file(self, model_name, page_id, feature_set):
        return "%s/data/temp/%s_%s_%s.annotated.gz" % (self.localdir, model_name, page_id, feature_set)
    
    def insert_new_page_annotated(self, url, version, is_body, model_name, content):
        self.c.execute('''INSERT INTO pages_annotated (url, timestamp, version, is_body, model_id) VALUES (?, DATETIME('now'), ?, ?, (SELECT id FROM models WHERE name=?))''', (url, version, "1" if is_body else "0", model_name))
        page_id = self.c.lastrowid
        self.conn.commit()

        fname = self.page_annotated_filename(model_name, page_id, is_body)
        assert(not(os.path.exists(fname)))
        fp = gzip.open(fname, 'wb')

        if type(content) == "str":
            fp.write(content)
        else:
            for line in content:
                fp.write(line)
            
        return page_id
    
    def update_page_annotated(self, page_id, url, version, is_body, model_name, content):
        self.c.execute('''UPDATE pages SET url=?, timestamp=DATETIME('now'), version=?, is_body=?, model_id=(SELECT id FROM models WHERE name=?)) WHERE id=? ''', (url, version,  "1" if is_body else "0", model_name, page_id))
        self.conn.commit()
        fname = page_annotated_file(model_name, page_id, is_body)
        os.system("rm %s" % fname)
        assert(not(os.path.exists(fname)))
        fp = gzip.open(fname, 'wb')
        fp.write(content)

    # Returns a list of page-files in desired order for tracking of crossvalidation folds
    def extract_dataset_files(self, model_name, feature_set, order_by="id"):
        self.c.execute("SELECT pa.id, pa.is_body FROM pages_annotated AS pa JOIN models ON pa.model_id=models.id WHERE name=? ORDER BY ?", (model_name, order_by))
        # fileinfo = map(lambda x: (self.page_annotated_filename(model_name, x[0], x[1] == 1), x[0]), self.c.fetchall())
        filelist = []
        for page_id, db_is_body in self.c.fetchall():
            # Check if feature_file exists already
            filelist.append(self.page_annotated_filename(model_name, page_id, db_is_body == 1))
        return filelist

    def make_experiment_datasets(self, file_list, model_name, trainsetf, develsetf, testsetreff, testsetf, feature_set, nrfolds, fold):
        training_set_, test_set = k_fold_cross_validation(file_list, nrfolds, fold)

        # Create 10% development set:
        cutoff = int(math.ceil(len(training_set_)*9/10))
        training_set = training_set_[:cutoff]
        devel_set = training_set_[cutoff:]
        
        self.build_data_set(model_name, trainsetf, training_set, feature_set);
        self.build_data_set(model_name, develsetf, devel_set, feature_set);
        self.build_data_set(model_name, testsetreff, test_set, feature_set);

        log("Creating test file '%s'\n" % testsetf)
        self.striplabel(testsetreff, testsetf)

    # Create an unlabeled version of a file by stripping its label
    def striplabel(self, inputf, targetf):
        # Build testfile by stripping the label from the test reference file
        fpr = gzip.open(inputf)
        fpw = gzip.open(targetf, "wb")
        for line in fpr:
            parts = line.split("\t")
            fpw.write("\t".join(parts[:len(parts)-1]))
            fpw.write("\n")
        fpr.close()
        fpw.close()
                            
    def build_data_set(self, model_name, target_file, inputlist, feature_set):
        featurefiles = []
        for inputfile in inputlist:
            # Check if feature_file exists already
            page_id = int(re.search("/%s_([0-9]+)" % model_name, inputfile).groups()[0])
            featurefile = self.page_feature_file(model_name, page_id, feature_set)
            assert(os.path.exists(inputfile))
            if not os.path.exists(featurefile):
                log("Creating feature file '%s'\n" % featurefile)
                if inputfile[-11:] == "htmlbody.gz":
                    inputpage = BeautifulSoup('<html><body>%s</body></html>' % gzip.open(inputfile).read())
                else:
                    inputpage = BeautifulSoup(gzip.open(inputfile))
                self.create_feature_file(inputpage, featurefile, feature_set, annotated=True)
            featurefiles.append(featurefile)
        log("Aggregating data set in '%s'\n" % target_file)
        os.system("zcat %s | gzip > %s" % (" ".join(featurefiles), target_file))
        log("done\n")

    def create_feature_file(self, inputpage, featurefile, feature_set, annotated=True):

        words, f_ortho1, f_ortho3, f_html, labels, sentences, token_nodes, node_index, tokens=preprocess_file(inputpage, feature_set, build_node_index = False)
        fp = gzip.open(featurefile, 'wb')
        for i in xrange(len(sentences)):              
            if sentences[i] == "\n":
                fp.write("\n")
            else:
                fp.write((sentences[i]+"\t"+labels[i]+"\n").encode('utf8'))

def extractlabel(line):
    parts = line.split("\t")
    return parts[-1].strip()

def labels(inputf):        
    if inputf[-3:] == ".gz":
        fp = gzip.open(inputf)
    else:
        fp = open(inputf)
    for line in fp:
        if line == "\n":
            continue
        yield extractlabel(line)
    fp.close()

def label_to_index(label, tagmap):
    if not tagmap.has_key(label):
        log("Warning: label '%s' not in tagset" % label)
        return None
    return tagmap[label]

def discrete_histogram(x):
    hist = {}    
    for xi in x:
        if not hist.has_key(xi):
            hist[xi] = 0
        hist[xi] += 1
    return hist

class IndRange:
    def __init__(self, start, end):
        assert(end > start)
        self.start = start
        self.end = end

    def indeces(self):
        return range(self.start, self.end)

    def __len__(self):
        return self.end - self.start - 1



# From http://code.activestate.com/recipes/521906-k-fold-cross-validation-partition/
def k_fold_cross_validation(X, K, k):
    """
    Generates K (training, validation) pairs from the items in X.
    
    Each pair is a partition of X, where validation is an iterable
    of length len(X)/K. So each training iterable is of length (K-1)*len(X)/K.
    """
    training = [x for i, x in enumerate(X) if i % K != k]
    validation = [x for i, x in enumerate(X) if i % K == k]
    return (training, validation)

def evaluate_results(referencef, predictedf, tagset=[]):
    tagset_ = set()
    for l in labels(referencef):
        tagset_.add(l)
    for l in labels(predictedf):
        tagset_.add(l)
    tagset = sorted(list(tagset_))

    tagmap = dict(zip(tagset, range(len(tagset))))
    pairs = zip(map(lambda l: label_to_index(l, tagmap), labels(referencef)), \
                    map(lambda l: label_to_index(l, tagmap), labels(predictedf)))
    pairs = filter(lambda p: p[0] is not None, pairs)
    referencelabels, predictedlabels = zip(*pairs)
    cm = confusion_matrix(referencelabels, predictedlabels)

    predicted_counts = numpy.sum(cm, axis=0)
    reference_counts = numpy.sum(cm, axis=1)

    correct_counts = numpy.array(numpy.diag(cm), dtype=numpy.float)

    precisions = numpy.zeros(correct_counts.shape)
    recalls = numpy.zeros(correct_counts.shape)
    fs = numpy.zeros(correct_counts.shape)

    ind = predicted_counts > 0
    precisions[ind] = correct_counts[ind] / predicted_counts[ind]

    ind = reference_counts > 0
    recalls[ind] = correct_counts[ind] / reference_counts[ind]    

    ind = precisions + recalls > 0
    fs[ind] = 2*precisions[ind]*recalls[ind] / (precisions[ind] + recalls[ind])

    return (precisions, recalls, fs, tagset)


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



def class_features(node):
    # Classname features   
    classname=''; classlong=""; classbrief= ""  
    if node.has_attr('class'): 
        classname=",".join(node['class'])
        if node.name == "span" and "WebAnnotator" in classname:          
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
            # Find the annotation label and add to 'labels' list
            if node.name == "span" and node.has_attr("class") and "WebAnnotator_" in node['class'][0]:
                label=node['class'][0].replace('WebAnnotator_', '')
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
        self._feature_nm = ['word', 'long', 'brief']
        self._feature_nm.extend(map(lambda s: s+"count", Ortho.namemap.values()))
        self._feature_nm.extend(map(lambda s: "has" + s, Ortho.namemap.values()))

    def extract(self, token):
        tlong, tbrief = Ortho.generalisation(token);
        chartypecounts = Ortho.countletters(tlong);

        ret = {'word': (token.lower(), '1'), 'long': (tlong, '1') ,'brief': (tbrief, '1') }
        for k in Ortho.namemap.keys():
            ret["%scount" % Ortho.namemap[k]] = ('', str(chartypecounts[k])) 
            ret["has%s" % Ortho.namemap[k]] = ('', str(int(chartypecounts[k] > 0)))

        return ret 
    
    def feature_names(self):
        return self._feature_nm
    

def write_testfiles(path, filename, sentences, labels):
    testfile = open(os.getcwd()+path+'/temp/'+filename+'.test','w')    
    testreferencefile = open(os.getcwd()+path+'/temp/'+filename+'.test.reference','w')    
    for i in range(len(sentences)):              
        testfile.write(sentences[i].encode('utf8'))        
        testreferencefile.write((sentences[i]+"\t"+labels[i]).encode('utf8'))
        if sentences[i] != "\n":
            testfile.write('\n')        
            testreferencefile.write('\n')            
    

def nodeblocks(retfile, tokens, filterf):
    c = 0
    curnode = tokens[0][2]

    # Gather the nodes that have non-O tags
    curtags = []
    curfilterstat = False;

    for line in retfile:
        if line == "\n":
            continue
        if not curnode is tokens[c][2]:
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

def modified_subtreelist(soup, s, taggings, node_pos):
    nodel = []
    lastpos = 0
    for startoffset, endoffset, tag in taggings:            
        startpos = node_pos[0][startoffset]
        endpos = node_pos[1][endoffset]
        nodel.append(soup.new_string(s[lastpos:startpos]))
        span = soup.new_tag('span')
        span['wa-subtypes'] = ""
        span['wa-type'] = tag
        span['class'] = "Semantify_%s" % tag
        span['semantify'] = "auto"
        span.string = s[startpos:endpos]
        nodel.append(span)
        lastpos = endpos
    nodel.append(soup.new_string(s[lastpos:]))
    return nodel


def apply_tagging(soup, nodes_to_tag, node_index):
    for node, taggings in nodes_to_tag:
        ml = modified_subtreelist(soup, node.string, taggings, node_index[node])
        node.replace_with(ml[0])
        for i in range(1, len(ml)):
            ml[i-1].insert_after(ml[i])
            

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

def parse_feature_set_desc(s):
    featuregroups = s.split("+")
    try:
        ret = map(lambda st: re.match("([a-z]+)([0-9])", st).groups(), featuregroups)
        ret = map(lambda x: (x[0], int(x[1])), ret)
        return ret
    except AttributeError:
        raise ValueError("'%s' is not a valid feature set description" % s)

def feature_set_to_feature_function(parsed_feature_set):
    feature_set_descr = []
    htmlfeaturefuns = []
    tokenfeaturefuns = []
    for feature_name, window_size in parsed_feature_set:
        if feature_name == "ortho":
            blockf = Ortho()
            tokenfeaturefuns.append(blockf)
            feature_set_descr.append((feature_name, window_size, blockf, (0, len(tokenfeaturefuns) - 1)))
        elif feature_name == "html":
            blockf = Descendants()
            htmlfeaturefuns.append(blockf)
            feature_set_descr.append((feature_name, window_size, blockf, (1, len(htmlfeaturefuns) - 1)))
    return (htmlfeaturefuns, tokenfeaturefuns, feature_set_descr)

def preprocess_file(page, feature_set, build_node_index=False):        
    nodes = []

    parsed_feature_set = parse_feature_set_desc(feature_set)
    htmlfeaturefuns, tokenfeaturefuns, feature_set_descr = feature_set_to_feature_function(parsed_feature_set)

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
            words.append(sent[t][0]["word"][0])
            
            line = []
            for feature_name, window_size, blockfeaturef, feature_addr in feature_set_descr: 
                if window_size == 1:
                    wstart = 0
                    wend = 0
                else:
                    wstart = -(window_size // 2);
                    wend = window_size // 2;
                line.append(window(wstart, wend, t, sent, blockfeaturef.feature_names(), feature_addr[0]))

            sentences.append("\t".join(line))

            labels.append(tags[c])
            c += 1
        sentencec += 1
        words.append('\n'); f_ortho1.append('\n'); f_ortho3.append('\n'); f_html.append('\n'); labels.append('\n'); sentences.append('\n')   


    print "Tokens after sentence split"
    print len(sentences), len(words),  len(f_ortho1),  len(f_ortho3),  len(f_html),  len(labels) 
    print len(tokens) + sentencec 
    assert(len(tokens) + sentencec == len(sentences))

    return words, f_ortho1,  f_ortho3, f_html, labels, sentences, nodes, node_index, tokens

    
def history(conn, model_name, path, filename):    
    trainfile=open(os.getcwd()+path+'/temp/'+filename+'.train','w')
    traindevelfile=open(os.getcwd()+path+'/temp/'+filename+'.train.devel','w') 
    lines=[]
    
    c = conn.cursor()   
    
    schema_id = str(1)
    tokens = []
    tags = []
    writingflag=0
    lines=[]

    c.execute("SELECT id, isbody FROM pages_annotated WHERE model_id=(SELECT id FROM models WHERE name=?)" % (model_name,))
    orig_files = []
    feature_files = []

    for values in c.fetchall():
        suffix = "htmlbody" if values[1] == 1 else "html"
        orig_files.append("data/index/%s_%s.%s.gz" % (model_name, values[0], suffix))
        feature_files.append("data/temp/%s_%s_%s.annotated.gz" % (model_name, values[0], feature_set))

    
    
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
    

def accuracy(path, filename, tagset):
    
    standardfile=open(os.getcwd()+path+'/temp/'+filename+'.test.reference')
    firstfile=open(os.getcwd()+path+'/temp/'+filename+'.test.prediction')
    predictiontracker=open(os.getcwd()+path+'/temp/'+filename+'.prediction.tracker', 'w')   
    
    
    standard=standardfile.read().splitlines()
    stan=[]
 
    
    for i in standard:
        line=i.split(' : ')
        tagindex=len(line)-1        
        if line[0] and not line[0]=='\n':
            line=line[tagindex].replace('1', '')
            line=line.replace('\n', '')     
            stan.append(line)
        
    first=firstfile.read().splitlines()
    file1=[]
    for i in first:
        line=i.split(' : ')
        tagindex=len(line)-1
        if line[0] and not line[0]=='\n':
            line=line[tagindex].replace('1\t', '')
            line=line.replace('\n', '')
            file1.append(line)
    
    exclude=['O', 'START', 'STOP']
    #tagset=[]
    a=0; b=0
    for i in range(len(stan)):
        if stan[i]==file1[i]:
            a=a+1
        predictiontracker.write(stan[i]); predictiontracker.write('\t')
        predictiontracker.write(file1[i]); predictiontracker.write('\t')
        predictiontracker.write('\n')
        #if not stan[i] in exclude and not stan[i] in tagset:
            #tagset.append(stan[i])
    predictiontracker.close()
            
    print "a= %s \tlen(stan)= %s " % (a, len(stan))
    f1=(a/len(stan))*100
    print 'Original model accuracy is : ', f1
    
    return tagset
        
def confusionmatrix(path, filename, tagset):

    predictionfile=open(os.getcwd()+path+'/temp/'+filename+'.prediction.tracker')
    
    #confusionfile=open(os.getcwd()+path+'/temp/'+filename+'.'+confusion+'.confusion', 'w')    
    
    
    prediction=predictionfile.read().splitlines()
    true=[]; predfull=[]
    pred=[]
    
    
    
    def replace(token,  order):
        absent=0;
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
        return token,  order
    
    order=[0]
    for i in range(len(prediction)):
        line=prediction[i].split('\t')   
        line[0],  order=replace(line[0],  order)
        if not line[0] in order:
            order.append(line[0])
        line[1],  order=replace(line[1],  order)
        true.append(line[0])
        predfull.append(line[1])
        #confusionfile.write(repr(line))
        #confusionfile.write('\n')       
    
    #confusionfile.close()        
    
    if not len(order)==len(tagset)+1:
        for i in range(len(tagset)+1):
            if not i in order:
                true.append(i)
                predfull.append(i)
                pred.append(i)
                
    #statistics=metrics.classification_report(true, predfull)           
    print  'Confusion matrix for Original model is :', confusion_matrix( true,  predfull)    
    
    return confusion_matrix(true,  predfull), true, predfull
