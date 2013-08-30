
import numpy
from parsers import *
      

class Data(object):

    # __init__
    def __init__(self, parser, feature_manager, state_manager, graph):

        self.parser = parser
        self.feature_manager = feature_manager
        self.state_manager = state_manager
        self.graph = graph

        return

    def process(self):

        pass

    
    def get_instance(self):

        pass



class TrainData(Data):

    # __init__
    def __init__(self, train_file, feature_manager, state_manager, graph):

        parser = TrainFileParser(train_file)

        self.size = parser.size

        super(TrainData, self).__init__(parser, feature_manager, state_manager, graph)

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
    def __init__(self, devel_file, feature_manager, state_manager, graph, size = None):

        parser = DevelFileParser(devel_file)

        self.size = parser.size

        super(DevelData, self).__init__(parser, feature_manager, state_manager, graph)

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
    def __init__(self, test_file, feature_manager, state_manager, graph, size = None):

        parser = TestFileParser(test_file)

        self.size = parser.size

        super(TestData, self).__init__(parser, feature_manager, state_manager, graph)

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
