
import re
import numpy
from parsers import *

class FeatureManager(object):

    # __init__
    def __init__(self, train_file, ssl_file, graph, max_len_substring):
        
        self.parser = TrainFileParser(train_file)
        self.graph = graph
        self.max_len_substring = max_len_substring

        self.ssl = None
        if ssl_file:
            self.ssl = self.process_ssl_file(ssl_file)

        self.features, self.num_features = self.process()
        
        
        return


    def process(self):
        
        self.parser.open()

        features = {'BIAS': 0}

        for instance_index in range(self.parser.size):

            observation, len_observation, state_set = self.parser.parse(instance_index)

            feature_sets = self.extract_observation_feature_sets(observation, len_observation) 
            
            for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
                
                for clique in self.graph.get_clique_set(len(observation), clique_set_index):

                    t_j = clique.position

                    # add feature 
                    for (feature, value) in feature_sets[t_j]:
                        if features.get(feature, -1) == -1:
                            features[feature] = len(features)

        self.parser.close()
                            
        return features, len(features)


    def make_feature_vector_set(self, observation, len_observation):

        feature_vector_set = {}

        feature_sets = self.extract_observation_feature_sets(observation, len_observation)

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):

            for clique in self.graph.get_clique_set(len(observation), clique_set_index):

                t_j = clique.position

                feature_set = feature_sets[t_j]

                feature_index_set = []
                activation_set = []
                for feature, activation in feature_set:
                    feature_index = self.features.get(feature, -1)
                    if feature_index > -1:
                        feature_index_set.append(feature_index)
                        activation_set.append(activation) 
                
                feature_vector = (numpy.array(feature_index_set, dtype=numpy.int32), numpy.array(activation_set, dtype=numpy.int32)) # fixme

                feature_vector_set[t_j] = feature_vector

        return feature_vector_set


    def extract_observation_feature_sets(self, observation, len_observation):

        # return features sets in dictionary
        feature_sets = {}
        
        feature_sets[0] = [('BIAS', 1), ('substring right <s>', 1)]
        feature_sets[len_observation-1] = [('BIAS', 1), ('substring right </s>', 1)]

        for t in range(1, len_observation-1):

            # bias
            feature_sets[t] = [('BIAS', 1)] 

            # left substring
            for start in range(max(t-self.max_len_substring, 0), t):
                feature = 'substring left ' + ''.join(observation[start:t])
                feature_sets[t].append((feature, 1))

            # right substring
            for stop in range(t+1, min(t+self.max_len_substring, len_observation)+1):
                feature = 'substring right ' + ''.join(observation[t:stop])
                feature_sets[t].append((feature, 1))

        if self.ssl:

            word = ''.join(observation[1:len_observation-1])
            
            d = self.ssl.get(word, -1)

            if d != -1:

                for ssl_id, values in d.items():

                    for t in range(1, len_observation-1):
                        
                        feature = '%s' % ssl_id
                        value = float(values[t-1])
                        feature_sets[t].append((feature, value))

        return feature_sets


    def process_ssl_file(self, ssl_file):

        ssl = {}

        for line in file(ssl_file):

            line = line.strip().split()

            word = line.pop(0)

            if word not in ssl: 
                ssl[word] = {}

            ssl_id = line.pop(0)            
            values = line

            ssl[word][ssl_id] = values

        return ssl

            
