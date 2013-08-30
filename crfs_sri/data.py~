
import numpy
from parsers import *
      

class Data(object):

    # __init__
    def __init__(self, parser, corpus_id, task_id, feature_manager, state_manager, graph, size = None):

        self.parser = parser
        self.corpus_id = corpus_id
        self.task_id = task_id
        self.feature_manager = feature_manager
        self.state_manager = state_manager
        self.graph = graph

        if size == None:
            self.size = parser.size
        else:
            self.size = int(float(size)/100*parser.size) # percentage of all

        return

    def process(self):

        pass

    
    def get_instance(self):

        pass



class TrainData(Data):

    # __init__
    def __init__(self, train_file, corpus_id, task_id, feature_manager, state_manager, graph, size = None):

        parser = TrainFileParser(train_file, corpus_id, task_id)

        super(TrainData, self).__init__(parser, corpus_id, task_id, feature_manager, state_manager, graph, size)

        self.id = 'train data'

        self.feature_vector_sets, self.observations, self.true_state_sets, self.true_state_index_sets, self.instance_index_set = self.process()
        self.preprocessed = True

        return


    def process(self):

        feature_vector_sets = []
        observations = []
        true_state_sets = []
        true_state_index_sets = []

        self.parser.open()

        for instance_index in range(self.parser.size):

            observation, len_observation, true_state_set = self.parser.parse(instance_index)

            feature_vector_set = self.feature_manager.make_feature_vector_set(observation, len_observation)

            true_state_index_set = self.state_manager.convert_state_set_to_state_index_set(true_state_set, len_observation)

            # add
            feature_vector_sets.append(feature_vector_set)
            observations.append(observation)
            true_state_sets.append(true_state_set)
            true_state_index_sets.append(true_state_index_set)

        self.parser.close()

        instance_index_set = range(self.size)
        import numpy.random
        numpy.random.seed(10)
        numpy.random.shuffle(instance_index_set)

        return feature_vector_sets, observations, true_state_sets, true_state_index_sets, instance_index_set


    def get_instance(self, instance_index, args = None):
        
        if self.preprocessed:

            observation = self.observations[instance_index]
            
            len_observation = len(observation)
            
            feature_vector_set = self.feature_vector_sets[instance_index]
            
            true_state_index_set = self.true_state_index_sets[instance_index]
            
            true_state_set = self.true_state_sets[instance_index]

        else:

            observation, len_observation, true_state_set = self.parser.parse(instance_index)
            
            feature_vector_set = self.feature_manager.make_feature_vector_set(observation, len_observation)
            
            true_state_index_set = self.state_manager.convert_state_set_to_state_index_set(true_state_set, len_observation)                

        return observation, len_observation, feature_vector_set, true_state_index_set, true_state_set



class DevelData(Data):

    # __init__
    def __init__(self, devel_file, corpus_id, task_id, feature_manager, state_manager, graph, size = None):

        parser = DevelFileParser(devel_file, corpus_id, task_id)

        super(DevelData, self).__init__(parser, corpus_id, task_id, feature_manager, state_manager, graph)

        self.id = 'devel data'

        self.feature_vector_sets, self.observations = self.process()
        self.preprocessed = True

        return


    def process(self):

        feature_vector_sets = []
        observations = []

        self.parser.open()

        for instance_index in range(self.parser.size):

            observation, len_observation = self.parser.parse(instance_index)

            feature_vector_set = self.feature_manager.make_feature_vector_set(observation, len_observation)

            # add
            feature_vector_sets.append(feature_vector_set)
            observations.append(observation)

        self.parser.close()

        return feature_vector_sets, observations


    def get_instance(self, instance_index, args = None):
        
        if self.preprocessed:

            observation = self.observations[instance_index]
                
            len_observation = len(observation)
                
            feature_vector_set = self.feature_vector_sets[instance_index]
                
        else:

            observation, len_observation, true_state_set = self.parser.parse(instance_index)

            feature_vector_set = self.feature_manager.make_feature_vector_set(observation, len_observation)

        return observation, len_observation, feature_vector_set



class TestData(Data):

    # __init__
    def __init__(self, test_file, corpus_id, task_id, feature_manager, state_manager, graph, size = None):

        parser = TestFileParser(test_file, corpus_id, task_id)

        super(TestData, self).__init__(parser, corpus_id, task_id, feature_manager, state_manager, graph)

        self.id = 'devel data'

        self.feature_vector_sets, self.observations = self.process()
        self.preprocessed = True
       
        return


    def process(self):

        feature_vector_sets = []
        observations = []

        self.parser.open()

        for instance_index in range(self.parser.size):

            observation, len_observation = self.parser.parse(instance_index)

            feature_vector_set = self.feature_manager.make_feature_vector_set(observation, len_observation)

            # add
            feature_vector_sets.append(feature_vector_set)
            observations.append(observation)

        self.parser.close()

        return feature_vector_sets, observations


    def get_instance(self, instance_index, args = None):
        
        if self.preprocessed:

            observation = self.observations[instance_index]
                
            len_observation = len(observation)
                
            feature_vector_set = self.feature_vector_sets[instance_index]
                
        else:

            observation, len_observation, true_state_set = self.parser.parse(instance_index)

            feature_vector_set = self.feature_manager.make_feature_vector_set(observation, len_observation)

        return observation, len_observation, feature_vector_set
