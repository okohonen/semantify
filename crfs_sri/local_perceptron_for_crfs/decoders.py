
from performance_measures import *

class Decoder(object):

    # __init__
    def __init__(self, inference_algorithm, graph, corpus_id, task_id):
        
        self.inference_algorithm = inference_algorithm
        self.graph = graph
        self.corpus_id = corpus_id
        self.task_id = task_id
        self.performance_measure = self.initialize_performance_measure(corpus_id, task_id, graph)

        # initialize performance measure

        return

    def initialize_performance_measure(self, corpus_id, task_id, graph):

        if task_id in ['tagging']:
            performance_measure = Accuracy(corpus_id, task_id)
        elif task_id in ['chunking-bio']:
            performance_measure = FMeasureBIO(corpus_id, task_id)
        elif task_id in ['chunking-io']:
            performance_measure = FMeasureIO(corpus_id, task_id)
        elif task_id in ['tagging-and-chunking-bio', 'X-tagging-and-chunking-bio', 'joint-tagging-and-chunking-bio']:
            performance_measure = AccuracyAndFMeasureBIO(corpus_id, task_id, tag_chain_index = 0, chunk_chain_index = 1)
        elif task_id in ['tagging-and-chunking-io', 'X-tagging-and-chunking-io', 'joint-tagging-and-chunking-io']:
            performance_measure = AccuracyAndFMeasureIO(corpus_id, task_id, tag_chain_index = 0, chunk_chain_index = 1)

        return performance_measure


    def write(self, observation, len_observation, map_state_set, FILE):

        for t in range(1, len_observation-1):
            
            if self.corpus_id in ['wsj', 'geniatb']:

                if self.task_id in ['tagging']:

                    line = '%s %s %s' % (observation[t], map_state_set[(0, t)], 'None')

                elif self.task_id in ['chunking-bio', 'chunking-io']:

                    line = '%s %s %s' % (observation[t], 'None', map_state_set[(0, t)])

                elif self.task_id in ['joint-tagging-and-chunking-bio', 'joint-tagging-and-chunking-io']:

                    line = '%s %s %s' % (observation[t], map_state_set[(0, t)].split()[0], map_state_set[(0, t)].split()[1])

                elif self.task_id in ['tagging-and-chunking-io', 'tagging-and-chunking-bio', 'X-tagging-and-chunking-io', 'X-tagging-and-chunking-bio']:

                    line = '%s %s %s' % (observation[t], map_state_set[(0, t)], map_state_set[(1, t)])

            else:

               line = '%s %s' % (observation[t], map_state_set[(0, t)])
                    
            FILE.write('%s\n' % line)

        FILE.write('\n')

        return


    def decode(self, parameters, data, prediction_file, reference_file = None):

        FILE = open(prediction_file, 'w') # fixme

        for instance_index in range(data.size):
            
            # get instance
            
            observation, len_observation, feature_vector_set = data.get_instance(instance_index)

            # inference

            if self.corpus_id in []: # uses tag dictionary

                map_state_index_set, map_state_set = self.inference_algorithm.compute_map_state_index_set(parameters, feature_vector_set, len_observation, observation)
            
            else:

                map_state_index_set, map_state_set = self.inference_algorithm.compute_map_state_index_set(parameters, feature_vector_set, len_observation)

            # write to file
            
            self.write(observation, len_observation, map_state_set, FILE)

        FILE.close()

        if reference_file != None:

             performance = self.performance_measure.evaluate(prediction_file, reference_file)

        else:

            performance = None


        return performance


