
from performance_measures import *


class Decoder(object):

    # __init__
    def __init__(self, inference_algorithm, graph, token_eval):
        
        self.inference_algorithm = inference_algorithm
        self.graph = graph
        self.performance_measure = PerformanceMeasure(token_eval)

        return


    def write(self, observation, len_observation, map_state_set, FILE):

        line = ''.join(observation[1:len_observation-1]) + '\t'

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                t = clique.position

                if t == 0 or t == len_observation-1:

                    continue

                if map_state_set[t] in ['B', 'S']:

                    if t == 1:                    

                        line += observation[t]

                    else:

                        line += ' ' + observation[t] 

                else:

                    line += observation[t]
        
        FILE.write('%s\n' % line)

        return


    def decode(self, parameters, data, prediction_file, reference_file = None):

        FILE = open(prediction_file, 'w')

        for instance_index in range(data.size):
            
            # get instance
            
            observation, len_observation, feature_vector_set = data.get_instance(instance_index)

            # inference

            map_state_index_set, map_state_set = self.inference_algorithm.compute_map_state_index_set(parameters, feature_vector_set, len_observation)

            # write to file
            
            self.write(observation, len_observation, map_state_set, FILE)

        FILE.close()

        if reference_file != None:

             performance = self.performance_measure.evaluate(prediction_file, reference_file)

        else:

            performance = None


        return performance


