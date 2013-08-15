

from data import *
from decoders import *
from feature_managers import *
from graphs import *
from inference_algorithms import *
from parsers import *
from performance_measures import *
from state_managers import *
from train_algorithms import *

import cPickle
import os
import copy
import gzip


class Model(object):

    # __init__
    def __init__(self):

        return


    def init(self):

        return


    def save(self, model_file):

        d = {'decoder' : self.decoder, \
                 'feature manager' : self.feature_manager, \
                 'graph' : self.graph, \
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
        self.graph = d['graph']
        self.hyperparameters = d['hyperparameters']
        self.parameters = d['parameters']
        self.state_manager = d['state manager']

        FILE.close()

        return


    def initialize_parameters(self, feature_manager, state_manager, graph):

        num_features = feature_manager.num_features
        
        if graph.id in ['non-structured-chain']:

            parameters = []
            num_parameters = 0

            for clique_set_index in graph.get_clique_set_index_set(size = 'single'):
                parameters.append(numpy.zeros((state_manager.num_states[clique_set_index], num_features), dtype=numpy.float32)) 
                num_parameters += state_manager.num_states[clique_set_index] * num_features

        else:
                
            parameters = []
            num_parameters = 0
                
            for clique_set_index in graph.get_clique_set_index_set(size = 'single'):
                parameters.append(numpy.zeros((state_manager.num_states[clique_set_index], feature_manager.num_features), dtype=numpy.float32)) 
                num_parameters += state_manager.num_states[clique_set_index] * num_features

            for clique_set_index in graph.get_clique_set_index_set(size = 'double'):
                parameters.append(numpy.zeros((state_manager.num_states[clique_set_index], feature_manager.num_features), dtype=numpy.float32)) 
                num_parameters += state_manager.num_states[clique_set_index] * num_features

        return parameters, num_parameters


    def train(self, graph_id, tagset_id, train_algorithm_id, train_file, devel_file, prediction_file, ssl_file, token_eval, verbose):

        # check data set sizes
        train_file_parser = TrainFileParser(train_file)
        devel_file_parser = TrainFileParser(devel_file)
        
        print "\ttrain set size:", train_file_parser.size
        print "\tdevel set size:", devel_file_parser.size
        print

        # initialize graph
        
        if graph_id == 'non-structured-chain':
            self.graph = NonStructuredChain()
        elif graph_id == 'first-order-chain':
            self.graph = FirstOrderChain()
        elif graph_id == 'second-order-chain':
            self.graph = SecondOrderChain()
       
        # initialize state manager

        if verbose:
            print "\ttag set:", tagset_id
            print
        
        if graph_id == 'non-structured-chain':
            self.state_manager = NonStructuredStateManager(train_file, self.graph, tagset_id)
        else:
            self.state_manager = StructuredStateManager(train_file, self.graph, tagset_id)

        # initialize decoder
        
        if graph_id == 'non-structured-chain':
            inference_algorithm = NonStructuredInference(self.graph, self.state_manager)
        elif graph_id == 'first-order-chain':
            inference_algorithm = ExactInference(self.graph, self.state_manager)
        elif graph_id == 'second-order-chain':
            inference_algorithm = LoopyBeliefPropagation(self.graph, self.state_manager)

        self.decoder = Decoder(inference_algorithm, self.graph, token_eval)

        # initialize hyper parameters

        hyperparameters = {'max len substring (delta)' : 1}

        # initialize performance trackers

        opt_performance = {'target measure' : None}
        convergence_threshold = 3

        while True:

            # initialize feature manager
        
            feature_manager = FeatureManager(train_file, ssl_file, self.graph, hyperparameters['max len substring (delta)'])

            if verbose:
                print "\tmax len substring (delta):", hyperparameters['max len substring (delta)'] 
                print "\tnumber of features:", feature_manager.num_features

            # initialize devel and train data sets
            
            train_data = TrainData(train_file, feature_manager, self.state_manager, self.graph, tagset_id)
            devel_data = DevelData(devel_file, feature_manager, self.state_manager, self.graph, token_eval)

            # initialize training algorithm

            if graph_id == 'non-structured-chain':
                inference_algorithm = NonStructuredInference(self.graph, self.state_manager)
            elif graph_id == 'first-order-chain':
                inference_algorithm = ExactInference(self.graph, self.state_manager)
            elif graph_id == 'second-order-chain':
                inference_algorithm = LoopyBeliefPropagation(self.graph, self.state_manager)

            if train_algorithm_id == 'perceptron':

                train_algorithm = Perceptron(inference_algorithm, self.graph, self.decoder)

            elif train_algorithm_id == 'maximum-likelihood':

                train_algorithm = MaximumLikelihood(inference_algorithm, self.graph, self.decoder)

            # train
                
            parameters, num_parameters = self.initialize_parameters(feature_manager, self.state_manager, self.graph)

            if verbose:
                print "\tnumber of parameters:", num_parameters

            parameters, hyperparameters, performance = train_algorithm.train(parameters, hyperparameters, train_data, devel_data, prediction_file, devel_file, verbose)

            if performance['target measure'] > opt_performance['target measure']:

                self.feature_manager = copy.deepcopy(feature_manager)
                self.parameters = copy.deepcopy(parameters)
                self.hyperparameters = copy.deepcopy(hyperparameters)
                opt_performance = copy.deepcopy(performance)
                
            # check if training is continued
            if hyperparameters['max len substring (delta)'] - self.hyperparameters['max len substring (delta)'] == convergence_threshold:
                
                break

            hyperparameters['max len substring (delta)'] += 1

            if verbose:
                print
            
        # print

        if verbose:
            print
            print '\toptimal %s on devel set: %.1f' % (opt_performance['target measure id'], opt_performance['target measure'])        
            print '\toptimal %s: %.0f' % ('max len substring (delta)', self.hyperparameters['max len substring (delta)'])
            print '\toptimal %s: %.0f' % ('passes over train set', self.hyperparameters['number of passes'])
            print 

        # decode devel data with optimized parameters         
        devel_data = DevelData(devel_file, self.feature_manager, self.state_manager, self.graph, token_eval)
        performance = self.decoder.decode(self.parameters, devel_data, prediction_file)

        return


    def apply(self, test_file, prediction_file, ssl_file, verbose):

        # initialize data
        
        if ssl_file:
            self.feature_manager.ssl = self.feature_manager.process_ssl_file(ssl_file)

        test_data = TestData(test_file, self.feature_manager, self.state_manager, self.graph)

        if verbose:
            print
            print "\ttest set size:", test_data.size
            print

        # decode

        performance = self.decoder.decode(self.parameters, test_data, prediction_file)

        return













