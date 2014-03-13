
import copy
import cPickle
import gzip
import numpy
from optparse import OptionParser
import os
import re
import time



class TrainAlgorithm(object):

    # __init__
    def __init__(self):

        return

    def get_id(self):
        return self.id


class Perceptron(TrainAlgorithm):
    # averaged perceptron (Collins, 2002)

    # __init__
    def __init__(self, inference_algorithm, decoder):
        
        super(Perceptron, self).__init__()
                                                             
        self.id = 'perceptron'

        self.inference_algorithm = inference_algorithm
        self.decoder = decoder

        return


    def train(self, parameters, 
              train_data, 
              devel_data, 
              prediction_file, 
              reference_file, 
              verbose):
        
        hyperparameters = {}
        cum_parameters = copy.deepcopy(parameters)
        hyperparameters['number of passes'] = 1
        hyperparameters['number of updates'] = 1

        opt_parameters = None
        opt_hyperparameters = None
        opt_performance = {'target measure' : None}        

        convergence_threshold = 3

        while(1):

            # make a pass over train data

            parameters, cum_parameters, hyperparameters, error_free = self.make_pass(train_data, parameters, cum_parameters, hyperparameters)
            
            parameters = self.compute_average_parameters(parameters, cum_parameters, hyperparameters)

            # decode devel data

            performance = self.decoder.decode(parameters, devel_data, prediction_file, reference_file)

            if verbose:
                print "\tpass index %d, %s (devel) %.1f" % (hyperparameters['number of passes'], performance['target measure id'], performance['target measure'])

            # check for termination 

            if performance['target measure'] > opt_performance['target measure']:
                
                opt_parameters = copy.copy(parameters)
                opt_hyperparameters = copy.copy(hyperparameters)
                opt_performance = copy.copy(performance)

            elif hyperparameters['number of passes'] - opt_hyperparameters['number of passes'] == convergence_threshold:

                    break

            parameters = self.reverse_parameter_averaging(parameters, cum_parameters, hyperparameters)
            hyperparameters['number of passes'] += 1

        return opt_parameters, opt_hyperparameters, opt_performance


    def make_pass(self, train_data, 
                  parameters, 
                  cum_parameters, 
                  hyperparameters):
        
        error_free = True

        for instance_index in range(train_data.size):            

            # get instance

            observation, len_observation, feature_vector_set, true_state_index_set, true_state_set = train_data.get_instance(instance_index)

            # inference 

            map_state_index_set, map_state_set = self.inference_algorithm.compute_map_state_index_set(parameters, feature_vector_set, len_observation)

            # update parameters

            parameters, cum_parameters, hyperparameters, update_required = self.update_parameters(parameters, cum_parameters, hyperparameters, map_state_index_set, true_state_index_set, feature_vector_set, len_observation)

            hyperparameters['number of updates'] += 1

            if update_required:

                error_free = False

        return parameters, cum_parameters, hyperparameters, error_free


    def update_parameters(self, parameters, 
                          cum_parameters, 
                          hyperparameters,
                          map_state_index_set, 
                          true_state_index_set, 
                          feature_vector_set, 
                          len_observation):
        
        num_updates = hyperparameters['number of updates']

        update_required = False

        for t in range(1, len_observation):

            map_state_index = map_state_index_set[(t-1, t)]
            true_state_index = true_state_index_set[(t-1, t)]
                        
            if map_state_index != true_state_index:
                        
                update_required = True

                feature_vector = feature_vector_set[t]
                feature_index_set, activation_set = feature_vector
                
                # update emission parameters
                
                map_state_index_j = map_state_index_set[t]
                true_state_index_j = true_state_index_set[t]
                        
                if map_state_index_j != true_state_index_j:

                    parameters[0][true_state_index_j, feature_index_set] += activation_set
                    parameters[0][map_state_index_j, feature_index_set] -= activation_set

                    cum_parameters[0][true_state_index_j, feature_index_set] += num_updates*activation_set
                    cum_parameters[0][map_state_index_j, feature_index_set] -= num_updates*activation_set

                # update transition parameters
                
                parameters[1][true_state_index] += 1
                parameters[1][map_state_index] -= 1

                cum_parameters[1][true_state_index] += num_updates
                cum_parameters[1][map_state_index] -= num_updates

                # update emission parameters

        return parameters, cum_parameters, hyperparameters, update_required


    def compute_average_parameters(self, parameters, cum_parameters, hyperparameters):

        num_updates = float(hyperparameters['number of updates'])

        parameters[0] -= cum_parameters[0]/num_updates
        parameters[1] -= cum_parameters[1]/num_updates

        return parameters


    def reverse_parameter_averaging(self, parameters, cum_parameters, hyperparameters): 

        num_updates = float(hyperparameters['number of updates'])

        parameters[0] += cum_parameters[0]/num_updates
        parameters[1] += cum_parameters[1]/num_updates

        return parameters


class StateManager(object):

    # __init__
    def __init__(self, train_file):

        self.parser = TrainFileParser(train_file)

        self.state_sets, self.num_states = self.process()

        return


    def process(self):

        # initialize

        self.parser.open()

        state_sets = [['START', 'STOP'], []]

        # fetch states from training data

        for instance_index in range(self.parser.size):

            observation, len_observation, true_state_set = self.parser.parse(instance_index)

            for t in range(1, len_observation):

                state = true_state_set[t]

                if state not in state_sets[0]:
                    state_sets[0].append(state)

        # make state transitions

        for state_i in state_sets[0]:
            for state_j in state_sets[0]:
                state_sets[1].append((state_i, state_j))

        # number of states

        num_states = [len(state_sets[0]), len(state_sets[1])]

        # close parser

        self.parser.close()

        return state_sets, num_states


    def convert_state_set_to_state_index_set(self, state_set, len_observation): 

        if state_set == None:
            
            state_index_set = None

        else:

            state_index_set = {} 

            for t in range(1, len_observation):

                state_i = state_set[t-1]
                state_j = state_set[t]

                try:
                        
                    state_index_set[t] = self.state_sets[0].index((state_j))

                except ValueError:
                    
                    state_index_set[t] = -1                    

                try:
                        
                    state_index_set[(t-1, t)] = self.state_sets[1].index((state_i, state_j))

                except ValueError:
                    
                    state_index_set[(t-1, t)] = -1                    

        return state_index_set


    def convert_state_index_set_to_state_set(self, state_index_set, len_observation): 

        state_set = {} 

        for t in range(1, len_observation):

            try:

                state_index = state_index_set[t]
                
            except:

                state_index = -1

            state_set[t] = self.state_sets[0][state_index]

            try:

                state_index = state_index_set[(t-1, t)]
                
            except:

                state_index = -1

            state_set[(t-1, t)] = self.state_sets[1][state_index]

        return state_set 





class Accuracy(object):

    # __init__
    def __init__(self):

        return

    def evaluate(self, prediction_file, reference_file):

        prediction_file_parser = PredictionFileParser(prediction_file)
        reference_file_parser = ReferenceFileParser(reference_file)

        prediction_file_parser.open()
        reference_file_parser.open()

        statistics = self.initialize_statistics()
        
        if prediction_file_parser.size != reference_file_parser.size:
            print 'fatal warning: prediction and reference sizes do not match: %d vs %d!' % (prediction_file_parser.size, reference_file_parser.size)
                
        for instance_index in range(prediction_file_parser.size):

            observation, len_observation, predicted_state_set = prediction_file_parser.parse(instance_index)
            observation, len_observation, true_state_set = reference_file_parser.parse(instance_index)

            statistics = self.update_statistics(statistics, predicted_state_set, true_state_set, observation, len_observation)
            
        performance = self.compute_performance(statistics)

        prediction_file_parser.close()
        reference_file_parser.close()

        return performance


    def initialize_statistics(self):

        statistics = {}
        statistics['num correct predictions'] = 0
        statistics['num predictions'] = 0
        
        return statistics


    def update_statistics(self, statistics, predicted_state_set, true_state_set, observation, len_observation):

        for t in range(1, len_observation-1):

            predicted_state = predicted_state_set[t]
            true_state = true_state_set[t]

            if predicted_state == true_state:

                statistics['num correct predictions'] += 1

            statistics['num predictions'] += 1                
                
        return statistics


    def compute_performance(self, statistics):

        acc = float(statistics['num correct predictions'])/statistics['num predictions']*100
        
        performance = {'target measure id' : None, 'target measure' : None, 'all' : {}}

        performance['target measure id'] = 'acc'
        performance['target measure'] = acc

        performance['all']['acc'] = acc

        return performance



class Parser(object):

    def __init__(self, data_file):

        self.data_file = data_file

        self.instance_positions, self.size = self.process()

        return

    def open(self):

        if self.data_file[-3:] == ".gz":
            self.FILE = gzip.open(self.data_file, 'r')
        else:
            self.FILE = open(self.data_file, 'r')

        return


    def close(self): 

        self.FILE.close()
        self.FILE = None
        
        return


    def process(self):

        self.open()

        instance_positions = []

        previous_line_was_empty = True
        
        while(1):

            position = self.FILE.tell()
            line = self.FILE.readline().strip() 

            if not line and previous_line_was_empty:
                
                break
            
            elif not line and not previous_line_was_empty:

                previous_line_was_empty = True

            elif line and previous_line_was_empty:

                instance_positions.append(position)
                
                previous_line_was_empty = False

            elif line and not previous_line_was_empty:

                previous_line_was_empty = False

        instance_positions = instance_positions

        self.close()

        return instance_positions, len(instance_positions)




class TrainFileParser(Parser):

    def __init__(self, data_file):

        super(TrainFileParser, self).__init__(data_file)

        return

    
    def parse(self, instance_index):

        self.FILE.seek(self.instance_positions[instance_index])
            
        observation = []
        output = {}

        output[0] = 'START' 
        observation = [['<s> : 1']]
                
        while(1):
                    
            line = self.FILE.readline().strip()
            
            if line:

                line = line.split('\t')
                output[len(observation)] = line[-1]
                observation.append(line[:-1])

            else:
                
                break
                            
        output[len(observation)] = 'STOP'
        observation.append(['</s> : 1'])

        return observation, len(observation), output


class DevelFileParser(Parser):

    def __init__(self, data_file):

        super(DevelFileParser, self).__init__(data_file)

        return

    
    def parse(self, instance_index):

        self.FILE.seek(self.instance_positions[instance_index])

        observation = [['<s> : 1']]
                
        while(1):
                    
            line = self.FILE.readline().strip()
            
            if line:

                line = line.split('\t')
                observation.append(line[:-1])

            else:
                
                break
                            
        observation.append(['</s> : 1'])

        return observation, len(observation)



class TestFileParser(Parser):

    def __init__(self, data_file):

        super(TestFileParser, self).__init__(data_file)

        return

    
    def parse(self, instance_index):

        self.FILE.seek(self.instance_positions[instance_index])

        observation = ['<s>']
                
        while(1):
                    
            line = self.FILE.readline().strip()
            
            if line:

                line = line.split('\t')
                observation.append(line)

            else:
                
                break
                            
        observation.append('</s>')

        return observation, len(observation)




class PredictionFileParser(Parser):

    def __init__(self, data_file):

        super(PredictionFileParser, self).__init__(data_file)

        return


    def parse(self, instance_index):

        self.FILE.seek(self.instance_positions[instance_index])

        observation = []
        output = {}

        output[0] = 'START' 
        observation = ['<s>']

        while(1):

            line = self.FILE.readline().strip()
            
            if line:

                line = line.split('\t')
                output[len(observation)] = line[-1]
                observation.append(line[:-1])

            else:
                
                break
                
        output[len(observation)] = 'STOP'
        observation.append('</s>')
            
        return observation, len(observation), output




class ReferenceFileParser(Parser):

    def __init__(self, data_file):

        super(ReferenceFileParser, self).__init__(data_file)

        return


    def parse(self, instance_index):

        self.FILE.seek(self.instance_positions[instance_index])

        observation = []
        output = {}

        output[0] = 'START' 
        observation = ['<s>']

        while(1):

            line = self.FILE.readline().strip()
            
            if line:

                line = line.split('\t')
                output[len(observation)] = line[-1]
                observation.append(line[:-1])

            else:
                
                break
                
        output[len(observation)] = 'STOP'
        observation.append('</s>')

        return observation, len(observation), output



class InferenceAlgorithm(object):

    def __init__(self, state_manager):

        self.state_manager = state_manager
        
        return

    def get_id(self):
        return self.id



class Viterbi(InferenceAlgorithm):

    def __init__(self, state_manager):

        super(Viterbi, self).__init__(state_manager)

        self.id = 'Viterbi'

        return

    def compute_map_state_index_set(self, parameters, feature_vector_set, len_observation):
        
        potential_vector_set = self.compute_potential_vector_set(parameters, feature_vector_set, len_observation)

        map_state_index_set = {}

        backtrack_pointers = -1*numpy.ones((len_observation, self.state_manager.num_states[0]))
                                           
        a = None
        
        for t in range(1, len_observation):
                                               
            ab = potential_vector_set[(t-1, t)]
            if a != None:
                a_ab = a.reshape(a.size, 1) + ab # broadcast
            else:
                a_ab = ab
            backtrack_pointers[t, :] = numpy.argmax(a_ab, 0)
            a = numpy.max(a_ab, 0)

        map_state_index_set[t] = int(numpy.argmax(a))

        # backward
                
        for t in range(len_observation-1, 0, -1):
                                          
            map_j = map_state_index_set[t] # t already has likeliest state
            map_i = int(backtrack_pointers[t, map_j])
            map_state_index_set[t-1] = map_i
            map_state_index_set[(t-1, t)] = int(map_i*self.state_manager.num_states[0] + map_j)

        map_state_set = self.state_manager.convert_state_index_set_to_state_set(map_state_index_set, len_observation)

        return map_state_index_set, map_state_set


    def compute_potential_vector_set(self, parameters, feature_vector_set, len_observation):

        # return this
        potential_vector_set = {}

        for t in range(1, len_observation):

            potential_vector = self.compute_potential_vector(parameters, feature_vector_set[t], transition=True)

            potential_vector = potential_vector.reshape((self.state_manager.num_states[0], self.state_manager.num_states[0]))            

            potential_vector_j = self.compute_potential_vector(parameters, feature_vector_set[t], transition=False)

            potential_vector_set[(t-1, t)] = potential_vector+potential_vector_j

        return potential_vector_set


    def compute_potential_vector(self, parameters, feature_vector, transition):

        feature_index_set, activation_set = feature_vector

        if transition:

            potential_vector = parameters[1]

        else:

            potential_vector = numpy.sum(parameters[0][:, feature_index_set]*activation_set, 1)

        return potential_vector




class FeatureManager(object):
    # __init__
    def __init__(self, train_file):
        
        self.parser = TrainFileParser(train_file)
        self.features, self.num_features = self.process()

        return


    def process(self):
        
        self.parser.open()

        features = {'BIAS': 0}

        for instance_index in range(self.parser.size):

            observation, len_observation, state_set = self.parser.parse(instance_index)

            feature_sets = self.extract_observation_feature_sets(observation, len_observation)
            
            for t in range(len_observation):
                
                # add feature 
                for (feature, value) in feature_sets[t]:
                    if features.get(feature, -1) == -1:
                        features[feature] = len(features)

        self.parser.close()

        return features, len(features)


    def make_feature_vector_set(self, observation, len_observation):

        feature_vector_set = {}

        feature_sets = self.extract_observation_feature_sets(observation, len_observation)

        for t in range(len_observation):

            feature_set = feature_sets[t]

            feature_index_set = []
            activation_set = []
            for feature, activation in feature_set:

                feature_index = self.features.get(feature, -1)

                if feature_index > -1:

                    feature_index_set.append(feature_index)
                    activation_set.append(activation) 
                
            feature_vector = (numpy.array(feature_index_set, dtype=numpy.int32), numpy.array(activation_set, dtype=numpy.int32))

            feature_vector_set[t] = feature_vector

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

                feature_id, value = element.split(' : ')
                
                #devutil.keyboard()                
                
                feature_sets[t].append((feature_id, float(value)))

        feature_sets.append([('BIAS', 1), ('</s>', 1)])

        return feature_sets

    

class Decoder(object):

    # __init__
    def __init__(self, inference_algorithm):
        
        self.inference_algorithm = inference_algorithm
        self.performance_measure = Accuracy()

        return


    def write(self, observation, len_observation, map_state_set, FILE):

        for t in range(1, len_observation-1):
            
            line = '\t'.join(observation[t]) + '\t' + map_state_set[t]

            FILE.write('%s\n' % line)

        FILE.write('\n')

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




class Data(object):

    # __init__
    def __init__(self, parser, feature_manager, state_manager):

        self.parser = parser
        self.feature_manager = feature_manager
        self.state_manager = state_manager

        return

    def process(self):

        pass

    
    def get_instance(self):

        pass



class TrainData(Data):

    # __init__
    def __init__(self, train_file, feature_manager, state_manager):

        parser = TrainFileParser(train_file)

        self.size = parser.size

        super(TrainData, self).__init__(parser, feature_manager, state_manager)

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
    def __init__(self, devel_file, feature_manager, state_manager):

        parser = DevelFileParser(devel_file)

        self.size = parser.size

        super(DevelData, self).__init__(parser, feature_manager, state_manager)

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
    def __init__(self, test_file, feature_manager, state_manager):

        parser = TestFileParser(test_file)

        self.size = parser.size

        super(TestData, self).__init__(parser, feature_manager, state_manager)

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




class CRF(object):

    # __init__
    def __init__(self):

        return


    def init(self):

        return


    def save(self, model_file):

        d = {'decoder' : self.decoder, \
                 'feature manager' : self.feature_manager, \
                 'hyperparameters' : self.hyperparameters, \
                 'parameters' : self.parameters, \
                 'state manager' : self.state_manager}

	FILE = gzip.GzipFile(model_file, 'wb')
	FILE.write(cPickle.dumps(d, 1))
	FILE.close()

        return


    def load(self, model_file):

	FILE = gzip.GzipFile(model_file, 'rb')

        d = cPickle.load(FILE)

        self.decoder = d['decoder']
        self.feature_manager = d['feature manager']
        self.hyperparameters = d['hyperparameters']
        self.parameters = d['parameters']
        self.state_manager = d['state manager']

        FILE.close()

        return


    def initialize_parameters(self, feature_manager, state_manager):

        parameters = []
        num_parameters = 0
                
        parameters.append(numpy.zeros((state_manager.num_states[0], feature_manager.num_features), dtype=numpy.float32)) 
        num_parameters += state_manager.num_states[0] * feature_manager.num_features

        parameters.append(numpy.zeros(state_manager.num_states[1], dtype=numpy.float32)) 
        num_parameters += state_manager.num_states[1]

        return parameters, num_parameters


    def train(self, train_file, 
              devel_file, 
              prediction_file,               
              verbose):

        print "\tpreprocess"

        # initialize state manager

        self.state_manager = StateManager(train_file)

        # initialize feature manager
    
        self.feature_manager = FeatureManager(train_file)

        # initialize devel and train data sets

        train_data = TrainData(train_file, self.feature_manager, self.state_manager)
        devel_data = DevelData(devel_file, self.feature_manager, self.state_manager)

        print '\ttrain data size:', train_data.size
        print '\tdevel data size:', devel_data.size
        print "\tnumber of features:", self.feature_manager.num_features

        # initialize decoder
            
        inference_algorithm = Viterbi(self.state_manager)

        self.decoder = Decoder(inference_algorithm)

        # initialize training algorithm
            
        inference_algorithm = Viterbi(self.state_manager)

        train_algorithm = Perceptron(inference_algorithm, self.decoder)

        # train

        initial_parameters, num_parameters = self.initialize_parameters(self.feature_manager, self.state_manager) 

        if verbose:
            print "\tnumber of parameters:", num_parameters
            print

        print "\ttrain"
        print
        print "\ttrain algorithm:", train_algorithm.id
        print
        
        self.parameters, self.hyperparameters, performance = train_algorithm.train(initial_parameters, train_data, devel_data, prediction_file, devel_file, verbose)

        # print

        print

        for key, value in self.hyperparameters.items():

            print "\t%s: %.1f" % (key, value)

        print 

        for key, value in performance['all'].items():

            print '\t%s (devel): %.2f' % (key, value)
            
            # acc_temp is collected for cross validation experiment purpose
            acc_temp=value
        print

        return self.feature_manager.num_features, acc_temp



    def apply(self, test_file, prediction_file, verbose):

        # initialize data

        test_data = TestData(test_file, self.feature_manager, self.state_manager)

        print
        print "\ttest set size:", test_data.size
        print

        # decode

        self.decoder.decode(self.parameters, test_data, prediction_file)

        return

   







if __name__ == "__main__":

    tic = time.clock()

    # parse options
    parser = OptionParser("Usage: %prog [options]")
    parser.add_option("--train_file", dest = "train_file", default = None)
    parser.add_option("--devel_file", dest = "devel_file", default = None)
    parser.add_option("--test_file", dest = "test_file", default = None)
    parser.add_option("--prediction_file", dest = "prediction_file", default = None)
    parser.add_option("--reference_file", dest = "reference_file", default = None)
    parser.add_option("--model_file", dest = "model_file", default = None)
    parser.add_option("--verbose", action = "store_true", dest = "verbose", default = False)

    (options, args) = parser.parse_args()

    # print options

    print "options"
    print "\ttrain file:", options.train_file
    print "\tdevel file:", options.devel_file
    print "\ttest file:", options.test_file
    print "\tprediction file:", options.prediction_file
    print "\treference file:", options.reference_file
    print "\tmodel file:", options.model_file
    print "\tverbose:", options.verbose
    print

    if options.train_file: # train model

        print "initialize model"
        m = CRF()
        print "done"
        print
        print "train model"
        print
        m.train(options.train_file, options.devel_file, options.prediction_file, options.verbose)
        print "done"
        print
        print "save model"
        print "\tmodel file:", options.model_file
        m.save(options.model_file)
        print "done"
        print
        print "time consumed in training:", time.clock() - tic
        print

    elif options.model_file != None and options.test_file != None: # load model and apply

        print
        print "initialize model"
        m = CRF()
        print "done"
        print

        print "load model"
        print "\tmodel file:", options.model_file
        m.load(options.model_file)
        print "done"
        print

        print "decode"
        m.apply(options.test_file, options.prediction_file, options.verbose)
        print "done"
        print        
        print "time consumed in decoding:", time.clock() - tic
        print
       
    elif options.prediction_file != None and options.reference_file != None: # evaluate a prediction file

        performance_measure = Accuracy()
        performance = performance_measure.evaluate(options.prediction_file, options.reference_file)

        for key, value in performance['all'].items():
      
            print '\t%s (devel): %.2f' % (key, value)

        print

        
        




