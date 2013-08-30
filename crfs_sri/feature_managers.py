
import re
import numpy

from parsers import * 


class FeatureManager(object):

    # __init__
    def __init__(self, train_file, graph):
        
        self.parser = TrainFileParser(train_file)
        self.graph = graph
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

                    (l_j, t_j) = clique.position

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

                (l_j, t_j) = clique.position

                feature_set = feature_sets[t_j]

                feature_index_set = []
                activation_set = []
                for feature, activation in feature_set:

                    feature_index = self.features.get(feature, -1)

                    if feature_index > -1:

                        feature_index_set.append(feature_index)
                        activation_set.append(activation) 
                
                feature_vector = (numpy.array(feature_index_set, dtype=numpy.int32), numpy.array(activation_set, dtype=numpy.int32))

                feature_vector_set[t_j] = feature_vector

        return feature_vector_set


    def extract_observation_feature_sets(self, observation, len_observation):

        # return features sets in dictionary
        feature_sets = []
        
        feature_sets.append([('BIAS', 1), ('<s>', 1)])

        for t in range(1, len_observation-1):

            feature_sets.append([])

            # bias
            feature_sets[t].append(('BIAS', 1))

            for element in observation[t]:

#                m = re.match('\(\((.*)\), \((.*)\)\)', element)                             
#                feature_id, value = m.group(1), m.group(2)

                feature_id, value = element.split(' : ')

                feature_sets[t].append((feature_id, float(value)))

        feature_sets.append([('BIAS', 1), ('</s>', 1)])

        return feature_sets

    
