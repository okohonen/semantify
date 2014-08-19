import devutil
import feature_file as ff
import random
import time
from crfs import CRF
import gzip
import os
from collections import defaultdict
import feature_file as ff
import cPickle
from multiprocessing import Process, Lock


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
    def __init__(self, storage_dir, model_name, feature_set, train_devel_splitter, page_index = None):
        self.storage_dir = storage_dir
        self.model_name = model_name
        self.feature_set = feature_set
        self.train_devel_splitter = train_devel_splitter
        self.train_file_name = "%s/%s_%s_train.gz" % (storage_dir, model_name, feature_set)
        self.devel_file_name = "%s/%s_%s_devel.gz" % (storage_dir, model_name, feature_set)
        self.devel_prediction_file_name = "%s/%s_%s_devel.prediction" % (storage_dir, model_name, feature_set)
        self.page_id_file_name = "%s/%s_%s_train_ids.bin" % (storage_dir, model_name, feature_set)

        self.page_index = page_index
        self.page_ids = []

        # Resumme from page_index
        if not(page_index is None):
            feature_f = page_index.get_current_model_annotated_feature_files(self.model_name, self.feature_set, rebuild_if_missing=False)
            self.page_ids = [f[0] for f in feature_f]
        else:
            assert(not(os.path.exists(self.train_file_name)))
            assert(not(os.path.exists(self.devel_file_name)))
        
        self.verbose = True
        self.trainfp = None
        self.develfp = None

        self.training_id = 1;
        self.trainlock = Lock()

    def set_verbose(self, verbose):
        self.verbose = verbose

    def _clear_incremental(self):
        if not(self.trainfp is None):
            self.trainfp.close()
            self.trainfp = None
        if os.path.exists(self.train_file_name):
            os.system("rm %s" % self.train_file_name)
        if not(self.develfp is None):
            self.develfp.close()
            self.develfp = None
        if os.path.exists(self.devel_file_name):
            os.system("rm %s" % self.devel_file_name)

    def _rebuild(self):
        if self.page_index is None:
            raise ValueError("Cannot perform updates without access to page index")
        self._clear_incremental()
        feature_files = self.page_index.get_current_model_annotated_feature_files(self.model_name, self.feature_set, rebuild_if_missing=True)
        for page_id, feature_fname in feature_files:
            print "Adding file %s" % feature_fname
            self._add_train_devel(ff.StringFeatureFileReader(gzip.open(feature_fname), "utf-8"))
        self.trainfp.close()
        self.trainfp = None
        self.develfp.close()
        self.develfp = None

    def _add_train_devel(self, feature_f):
        if self.trainfp is None:
            self.trainfp = ff.StringFeatureFileWriter(gzip.open(self.train_file_name, "a"))
        if self.develfp is None:
            self.develfp = ff.StringFeatureFileWriter(gzip.open(self.devel_file_name, "a"))
        self.train_devel_splitter.apply(feature_f, self.trainfp, self.develfp)

    def incremental_train(self, feature_f, page_id, model_file=None):
        if page_id in self.page_ids:
            # Update, we must rebuild
            print "update, must rebuild training file"
            self._rebuild()
            print "done"
        else:        
            # Insert, we can just add to existing training file
            self._add_train_devel(feature_f)
            self.trainfp.close()
            self.trainfp = None
            self.develfp.close()
            self.develfp = None            
            if not(self.page_index is None):
                self.page_ids.append(page_id)

        if model_file is None:
            model_file = "%s/%s_%s_model.bin" % (self.storage_dir, self.model_name, self.feature_set)
        
        # Create own process for training to avoid blocking too long
        # Get unique id for training event
        my_id = self._get_training_id()
        train_file_name, devel_file_name, devel_prediction_file_name, model_file_name = self._create_unique_train_set(my_id, self.train_file_name, self.devel_file_name, self.devel_prediction_file_name, model_file)
 
        p = Process(target=train_crf, args = (my_id, self.trainlock, train_file_name, devel_file_name, devel_prediction_file_name, model_file_name, model_file, self.verbose))
        p.start()

    def _get_training_id(self):
        self.training_id += 1
        return self.training_id

    def _create_unique_train_set(self, my_id, *args):
        ret = []
        for f in args:
            parts = f.split(".")
            newfile = "%s.%d.%s" % (".".join(parts[0:-1]), my_id, parts[-1])
            if os.path.exists(f):
                os.system("cp %s %s" % (f, newfile))
            ret.append(newfile)
        print "Created training set " + ", ".join(ret)
        return ret

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


# Not part of class to simplify multithreading
def train_crf(my_id, trainlock, train_file_name, devel_file_name, devel_prediction_file_name, model_file, true_model_file, verbose):

    trainlock.acquire()
    try:
        # Check that we are still the newest guy on the block
        if is_newest_training(my_id, train_file_name):
            print "I'm newest, training"
            print (my_id, trainlock, train_file_name, devel_file_name, devel_prediction_file_name)
            t = time.time()
        
            print "initialize model"
            m = CRF()
            print "done"
            print
            print "train model"
            
            m.train(train_file_name, devel_file_name, devel_prediction_file_name, verbose)
            print "done"    
            print
            print "save model"
            m.save(model_file)
            print "done"
            print                
            #print accuracy                
            elapsed=time.time()-t
            print 'File', train_file_name, 'handled in:',  elapsed
        
            os.system("cp %s %s" % (model_file, true_model_file))
        else:
            print "Not newest %d, skipping training" % my_id
    finally:
        trainlock.release()
        cleanup_files(train_file_name, devel_file_name, devel_prediction_file_name, model_file)

def cleanup_files(*args):
    print "Cleaning up training files: %s" % ", ".join(args)
    for a in args:
        os.system("rm %s" % a)

# Check if this training_file is the latest
def is_newest_training(my_id, training_file):
    parts = training_file.split(".")
    pattern = "%s.*.%s" % (".".join(parts[0:-2]), parts[-1])
    fp = os.popen("ls -t %s" % pattern)
    for line in fp:
        parts = line.split(".")
        print "I %d Found file %s" % (my_id, parts[-2])
        if int(parts[-2]) > my_id:
            return False
    return True
