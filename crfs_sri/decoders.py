
from performance_measures import *

class Decoder(object):

    # __init__
    def __init__(self, inference_algorithm, graph, performance_measure_id):
        
        self.inference_algorithm = inference_algorithm
        self.graph = graph
        self.performance_measure = self.initialize_performance_measure(performance_measure_id, graph)

        return

    def initialize_performance_measure(self, performance_measure_id, graph):

        if performance_measure_id == 'accuracy':
            performance_measure = Accuracy()
        elif performance_measure_id == 'f-measure':
            performance_measure = FMeasureBIO()
        elif performance_measure_id == 'f-measure-io':
            performance_measure = FMeasureIO()

        return performance_measure


    def write(self, observation, len_observation, map_state_set, FILE):

        for t in range(1, len_observation-1):

#            print "DEBUG:", observation[t]

            line = '\t'.join(observation[t]) + '\t' + map_state_set[(0, t)]

#            print "DEBUG:", line

            FILE.write('%s\n' % line)

        FILE.write('\n')

        return


    def decode(self, parameters, data, prediction_file, reference_file = None, num_subsets = 1):

        FILE = open(prediction_file, 'w') # fixme

        for instance_index in range(data.size):
            
            # get instance
            
            observation, len_observation, feature_vector_set = data.get_instance(instance_index)

            # inference

            map_state_index_set, map_state_set = self.inference_algorithm.compute_map_state_index_set(parameters, feature_vector_set, len_observation)

            # write to file
            
            self.write(observation, len_observation, map_state_set, FILE)

        FILE.close()

        if reference_file != None:

             performance = self.performance_measure.evaluate(prediction_file, reference_file, num_subsets)

        else:

            performance = None


        return performance


