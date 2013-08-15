
import numpy
from parsers import *
      

class Data(object):

    # __init__
    def __init__(self, parser, feature_manager, state_manager, graph):

        self.parser = parser
        self.feature_manager = feature_manager
        self.state_manager = state_manager
        self.graph = graph

        self.size = self.parser.size

        return

    def process(self):

        pass

    
    def get_instance(self):

        pass



class TrainData(Data):

    # __init__
    def __init__(self, train_file, feature_manager, state_manager, graph, tagset_id):

        parser = TrainFileParser(train_file, tagset_id)

        super(TrainData, self).__init__(parser, feature_manager, state_manager, graph)

        self.id = 'train data'

        self.feature_vector_sets, self.observations, self.true_state_sets, self.true_state_index_sets, self.instance_index_set = self.process()

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
        
        observation = self.observations[instance_index]
        
        len_observation = len(observation)
        
        feature_vector_set = self.feature_vector_sets[instance_index]
        
        true_state_index_set = self.true_state_index_sets[instance_index]
        
        true_state_set = self.true_state_sets[instance_index]

        return observation, len_observation, feature_vector_set, true_state_index_set, true_state_set



class DevelData(Data):

    # __init__
    def __init__(self, devel_file, feature_manager, state_manager, graph, token_eval):

        parser = DevelFileParser(devel_file, token_eval)

        super(DevelData, self).__init__(parser, feature_manager, state_manager, graph)

        self.id = 'devel data'

        self.feature_vector_sets, self.observations = self.process()

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
        
        observation = self.observations[instance_index]
        
        len_observation = len(observation)
                
        feature_vector_set = self.feature_vector_sets[instance_index]
                
        return observation, len_observation, feature_vector_set



class TestData(Data):

    # __init__
    def __init__(self, test_file, feature_manager, state_manager, graph):

        parser = TestFileParser(test_file)

        super(TestData, self).__init__(parser, feature_manager, state_manager, graph)

        self.id = 'test data'

        self.feature_vector_sets, self.observations = self.process()
       
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
        
        observation = self.observations[instance_index]
                
        len_observation = len(observation)
                
        feature_vector_set = self.feature_vector_sets[instance_index]
                
        return observation, len_observation, feature_vector_set
