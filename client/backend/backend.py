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

from feature_file import labels
import feature_file as ff

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

    def get_tmpdir(self):
        return "%s/data/temp" % self.localdir

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
        assert(False)
        self.c.execute('''UPDATE pages_annotated SET url=?, timestamp=DATETIME('now'), version=?, is_body=?, model_id=(SELECT id FROM models WHERE name=?)) WHERE id=? ''', (url, version,  "1" if is_body else "0", model_name, page_id))
        self.conn.commit()
        fname = page_annotated_file(model_name, page_id, is_body)
        os.system("rm %s" % fname)
        assert(not(os.path.exists(fname)))
        fp = gzip.open(fname, 'wb')
        fp.write(content)

    def find_page_id(self, url, model_id):
        self.c.execute("SELECT id FROM pages_annotated WHERE url=? AND model_id=? ORDER BY version DESC", (url, model_id))
        r = self.c.fetchone()                
        if r is None:
            return None
        else:
            return r[0]

    # Returns a list of page-files in desired order for tracking of crossvalidation folds
    def extract_dataset_files(self, model_name, feature_set, order_by="id"):
        self.c.execute("SELECT pa.id, pa.is_body FROM pages_annotated AS pa JOIN models ON pa.model_id=models.id WHERE name=? ORDER BY ?", (model_name, order_by))
        # fileinfo = map(lambda x: (self.page_annotated_filename(model_name, x[0], x[1] == 1), x[0]), self.c.fetchall())
        filelist = []
        for page_id, db_is_body in self.c.fetchall():
            # Check if feature_file exists already
            filelist.append(self.page_annotated_filename(model_name, page_id, db_is_body == 1))
        return filelist

    #    def get_training_test_devel_split(self, file_list, nrfolds, fold, develratio):
        
        

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
        fp = gzip.open(featurefile, 'wb')
        for sent in self.extract_features(inputpage, feature_set, annotated).sentences():
            for tok in sent:
                fp.write(tok.encode('utf8'))        


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

def cm_to_prf(cm):
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

    return (precisions, recalls, fs)

def evaluate_results(referencef, predictedf, tagset):
    # Add possible tags from the tagger
    tagset.extend(['START', 'STOP'])

    tagmap = dict(zip(tagset, range(len(tagset))))
    pairs = zip(map(lambda l: label_to_index(l, tagmap), labels(referencef)), \
                    map(lambda l: label_to_index(l, tagmap), labels(predictedf)))
    pairs = filter(lambda p: p[0] is not None, pairs)
    referencelabels, predictedlabels = zip(*pairs)
    cm = confusion_matrix(referencelabels, predictedlabels, range(len(tagset)))

    precisions, recalls, fs = cm_to_prf(cm)

                

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
