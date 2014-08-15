import devutil
import feature_file as ff
import random
import time
from crfs import CRF
import gzip
import os
from collections import defaultdict
import feature_file as ff

class RandomTrainDevelSplitter:
    def __init__(self, devel_probability):
        self.devel_probability = devel_probability;
    
    def apply(self, input_ff, train_set, devel_set):
        for lines in input_ff.sentences():
            if random.random() < self.devel_probability:
                devel_set.append_sentence(lines)
            else:
                train_set.append_sentence(lines)

class ModuloTrainDevelSplitter:
    def __init__(self, modulo):
        self.mod = modulo
        self.tagcounts = defaultdict(int)
    
    def apply(self, input_ff, train_set, devel_set):
        for lines in input_ff.sentences():
            labels = map(ff.extractlabel, lines)
            devel = False
            for l in set(labels):
                self.tagcounts[l] += 1
                # Use 3 to get devel started somewhat quickly
                if self.tagcounts[l] % self.mod == 3:
                    devel = True
            if devel:
                devel_set.append_sentence(lines)
            else:
                train_set.append_sentence(lines)

class IncrementalTraining:
    def incremental_train(self, feature_fp):
        pass

    def apply_model(self, test_file_name, test_prediction_file_name):
        pass

class TrainingFileBuilderIncrementalTraining(IncrementalTraining):
    def __init__(self, storage_dir, model_name, train_devel_splitter, resuming=False):
        self.storage_dir = storage_dir
        self.model_name = model_name
        self.train_devel_splitter = train_devel_splitter
        self.train_file_name = "%s/%s_train.gz" % (self.storage_dir, self.model_name)
        self.devel_file_name = "%s/%s_devel.gz" % (self.storage_dir, self.model_name)
        if not(resuming):
            assert(not(os.path.exists(self.train_file_name)))
            assert(not(os.path.exists(self.devel_file_name)))
        
        ff.StringFeatureFileWriter(open("%s/%s_devel.gz" % (self.storage_dir, self.model_name), "a"))
        self.verbose = False

    def set_verbose(self, verbose):
        self.verbose = verbose

    def incremental_train(self, feature_f, devel_prediction_file, model_file):
        self.train_devel_splitter.apply(feature_f, ff.StringFeatureFileWriter(gzip.open(self.train_file_name, "a")), ff.StringFeatureFileWriter(gzip.open(self.devel_file_name, "a")))
        
        t = time.time()
        
        print "initialize model"
        m = CRF()
        print "done"
        print
        print "train model"
        
        m.train(self.train_file_name, self.devel_file_name, devel_prediction_file, self.verbose)
        print "done"    
        print
        print "save model"
        m.save(model_file)
        print "done"
        print                
        #print accuracy                
        elapsed=time.time()-t
        print 'File', self.train_file_name, 'handled in:',  elapsed

    def apply(self, model_file, test_file, test_prediction_file):
        t = time.time()

        m=CRF()
        m.load(model_file)
        print "done"
        print
        print "apply model"
        print (test_file, test_prediction_file, self.verbose)
        #m.apply(test_file, test_prediction_file, test_reference_file, verbose)
        m.apply(test_file, test_prediction_file, self.verbose)
        print "done"
        print
        
        elapsed=time.time()-t
        print 'File', test_file, 'handled in:',  elapsed

    
