from crfs import CRF
import os

# Wrapper class that can be applied to tag pages, model must pre-exist to be applicable
# Writes files into the the directory given in the first constructor argument

class TaggingModel:
    def __init__(self, storage_dir, model_name, feature_set):
        self.storage_dir = storage_dir
        self.model_name = model_name
        self.feature_set = feature_set
        self.model_fname = "%s/%s_%s_model.bin" % (storage_dir, model_name, feature_set)
        if not(os.path.exists(self.model_fname)):
            raise ValueError("Model file '%s' does not exist" % self.model_fname)

    def tag(self, page):
        test_fname = "%s/%s_%s.test.gz" % (self.storage_dir, self.model_name, self.feature_set)
        test_prediction_fname = "%s/%s_%s.test.prediction" % (self.storage_dir, self.model_name, self.feature_set)
        verbose = True;
        
        page.write_feature_file(test_fname)

        print "load model"
        m=CRF()
        m.load(self.model_fname)
        print "done"
        print
        print "apply model"
        print (test_fname, test_prediction_fname)
        
        m.apply(test_fname, test_prediction_fname, verbose)
        print "done"
        print
            
        print "Reading in prediction file"
        print

        return open(test_prediction_fname)


