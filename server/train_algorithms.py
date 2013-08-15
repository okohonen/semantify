
import numpy
import copy
import os


class TrainAlgorithm(object):

    # __init__
    def __init__(self):

        return

    def get_id(self):
        return self.id





class Perceptron(TrainAlgorithm):
    # averaged perceptron (Collins, 2002)

    # __init__
    def __init__(self, inference_algorithm, graph, decoder):
        
        super(Perceptron, self).__init__()
                                                             
        self.id = 'perceptron'

        self.inference_algorithm = inference_algorithm
        self.graph = graph
        self.decoder = decoder

        return


    def train(self, parameters, 
              hyperparameters, 
              train_data, 
              devel_data, 
              prediction_file, 
              reference_file, 
              verbose):
        
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

            if self.inference_algorithm.id in ['pseudo inference', 'piecewise-pseudo (factor-as-piece) inference', 'piecewise-pseudo (chain-as-piece) inference']:
                map_state_index_set, map_state_set = self.inference_algorithm.compute_map_state_index_set(parameters, feature_vector_set, len_observation, true_state_index_set)
            else:
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

        if self.inference_algorithm.id in ['non-structured inference']:

            update_required = False
            
            for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'): 
                    
                for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                    map_state_index = map_state_index_set[clique.position]
                    true_state_index = true_state_index_set[clique.position]
                
                    if map_state_index != true_state_index:

                        t = clique.position
                        
                        feature_vector = feature_vector_set[t]
                        (feature_index_set, activation_set) = feature_vector

                        # update parameters
                        parameters[clique_set_index][true_state_index, feature_index_set] += activation_set
                        parameters[clique_set_index][map_state_index, feature_index_set] -= activation_set

                        # update cumulative parameters                       
                        cum_parameters[clique_set_index][true_state_index, feature_index_set] += num_updates*activation_set
                        cum_parameters[clique_set_index][map_state_index, feature_index_set] -= num_updates*activation_set

                        update_required = True

        elif self.inference_algorithm.id in ['exact inference', 'loopy belief propagation']:
           
            update_required = False

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'): 

                for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                    map_state_index = map_state_index_set[clique.position]
                    true_state_index = true_state_index_set[clique.position]
                        
                    if map_state_index != true_state_index:

                        t = clique.position
                        
                        feature_vector = feature_vector_set[t]
                        (feature_index_set, activation_set) = feature_vector

                        # update parameters
                        parameters[clique_set_index][true_state_index, feature_index_set] += activation_set
                        parameters[clique_set_index][map_state_index, feature_index_set] -= activation_set
                            
                        # update cumulative parameters                       
                        cum_parameters[clique_set_index][true_state_index, feature_index_set] += num_updates*activation_set
                        cum_parameters[clique_set_index][map_state_index, feature_index_set] -= num_updates*activation_set

                        update_required = True

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'): 

                for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                    map_state_index = map_state_index_set[clique.position]
                    true_state_index = true_state_index_set[clique.position]
                        
                    if map_state_index != true_state_index:

                        t_i, t_j = clique.position

                        feature_vector = feature_vector_set[t_j]
                        (feature_index_set, activation_set) = feature_vector

                        # update parameters
                        parameters[clique_set_index][true_state_index, feature_index_set] += activation_set
                        parameters[clique_set_index][map_state_index, feature_index_set] -= activation_set
                            
                        # update cumulative parameters                       
                        cum_parameters[clique_set_index][true_state_index, feature_index_set] += num_updates*activation_set
                        cum_parameters[clique_set_index][map_state_index, feature_index_set] -= num_updates*activation_set

        elif self.inference_algorithm.id in ['piecewise (factor-as-piece) inference']:
           
            update_required = False

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'): 

                clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)
                
                for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                    map_state_index = map_state_index_set[clique.position]
                    true_state_index = true_state_index_set[clique.position]
                        
                    if map_state_index != true_state_index:

                        t_i, t_j = clique.position
                        
                        feature_vector = feature_vector_set[t_j]
                        (feature_index_set, activation_set) = feature_vector

                        # update parameters
                        parameters[clique_set_index][true_state_index, feature_index_set] += activation_set
                        parameters[clique_set_index][map_state_index, feature_index_set] -= activation_set
                            
                        # update cumulative parameters                       
                        cum_parameters[clique_set_index][true_state_index, feature_index_set] += num_updates*activation_set
                        cum_parameters[clique_set_index][map_state_index, feature_index_set] -= num_updates*activation_set

                        map_state_index_j = map_state_index_set[(t_j, clique.position)]
                        true_state_index_j = true_state_index_set[t_j]
                            
                        if map_state_index_j != true_state_index_j:

                            # update parameters
                            parameters[clique_set_index_j][true_state_index_j, feature_index_set] += activation_set
                            parameters[clique_set_index_j][map_state_index_j, feature_index_set] -= activation_set
                                
                            # update cumulative parameters                       
                            cum_parameters[clique_set_index_j][true_state_index_j, feature_index_set] += num_updates*activation_set
                            cum_parameters[clique_set_index_j][map_state_index_j, feature_index_set] -= num_updates*activation_set

                        update_required = True

        return parameters, cum_parameters, hyperparameters, update_required


    def compute_average_parameters(self, parameters, cum_parameters, hyperparameters):

        num_updates = float(hyperparameters['number of updates'])

        if self.inference_algorithm.id in ['non-structured inference']:

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
                parameters[clique_set_index] -= cum_parameters[clique_set_index]/num_updates

        else:

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'all'):
                parameters[clique_set_index] -= cum_parameters[clique_set_index]/num_updates

        return parameters


    def reverse_parameter_averaging(self, parameters, cum_parameters, hyperparameters): 

        num_updates = float(hyperparameters['number of updates'])

        if self.inference_algorithm.id in ['non-structured inference']:

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
                parameters[clique_set_index] += cum_parameters[clique_set_index]/num_updates

        else:

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'all'):
                parameters[clique_set_index] += cum_parameters[clique_set_index]/num_updates

        return parameters







class MaximumLikelihood(TrainAlgorithm):
    #  maximum likelihood training with a fixed learning rate (Vishwanathan et al., 2006)

    def __init__(self, 
                 inference_algorithm, 
                 graph, 
                 decoder):
        
        super(MaximumLikelihood, self).__init__()

        self.inference_algorithm = inference_algorithm
        self.graph = graph
        self.decoder = decoder

        self.id = 'fixed learning rate maximum likelihood training with %s' % inference_algorithm.id

        return


    def train(self, parameters, 
              hyperparameters, 
              train_data, 
              devel_data, 
              prediction_file, 
              reference_file, 
              verbose):
        
        cum_parameters = copy.deepcopy(parameters)

        hyperparameters['number of passes'] = 1
        hyperparameters['instance index'] = 1
        hyperparameters['regularization coefficient'] =  0.1 
        hyperparameters['learning rate'] = 0.1
        hyperparameters['minibatch size'] = 10

        opt_parameters = None
        opt_hyperparameters = None
        opt_performance = {'target measure' : None}        

        convergence_threshold = 3

        while(1):

            # make a pass over train data

            parameters, hyperparameters = self.make_pass(train_data, parameters, hyperparameters)
            
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

            hyperparameters['number of passes'] += 1

        return opt_parameters, opt_hyperparameters, opt_performance


    def make_pass(self, train_data, 
                  parameters, 
                  hyperparameters):
        
        minibatch = []

        for instance_index in train_data.instance_index_set:

            # get instance

            observation, len_observation, feature_vector_set, true_state_index_set, true_state_set = train_data.get_instance(instance_index)

            # inference 

            marginal_vector_set = self.inference_algorithm.compute_marginal_vector_set(parameters, feature_vector_set, len_observation)

           # update parameters

            if minibatch != [] and (instance_index % hyperparameters['minibatch size'] == 0 or instance_index == train_data.size-1):
                parameters, hyperparameters = self.regularize(parameters, hyperparameters, len(minibatch), train_data.size)
                parameters, hyperparameters = self.update_parameters_with_minibatch(parameters, hyperparameters, minibatch)
                minibatch = []
            else:
                minibatch.append((marginal_vector_set, true_state_index_set, feature_vector_set, len_observation))

            hyperparameters['instance index'] += 1

        return parameters, hyperparameters


    def regularize(self, parameters,
                   hyperparameters,
                   minibatch_size,
                   train_data_size):

        C = hyperparameters['regularization coefficient']        

        learning_rate = hyperparameters['learning rate']

        if self.inference_algorithm.id in ['nonstructured inference']:

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'): 
                parameters[clique_set_index] -= learning_rate*minibatch_size/train_data_size*C*parameters[clique_set_index] # l2

        else:

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'all'):
                parameters[clique_set_index] -= learning_rate*minibatch_size/train_data_size*C*parameters[clique_set_index] # l2

        return parameters, hyperparameters


    def update_parameters_with_minibatch(self, parameters, hyperparameters, minibatch):

        for (marginal_vector_set, true_state_index_set, feature_vector_set, len_observation) in minibatch:

            parameters, hyperparameters = self.update_parameters(parameters, hyperparameters, marginal_vector_set, true_state_index_set, feature_vector_set, len_observation)

        return parameters, hyperparameters


    def update_parameters(self, parameters,
                          hyperparameters,
                          marginal_vector_set, 
                          true_state_index_set, 
                          feature_vector_set, 
                          len_observation): 

        learning_rate = hyperparameters['learning rate']

        if self.inference_algorithm.id in ['nonstructured inference']:

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'): 

                for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                    marginal_vector = marginal_vector_set[clique.position]
                    true_state_index = true_state_index_set[clique.position]
                    num_states = marginal_vector.size
                
                    t = clique.position

                    feature_vector = feature_vector_set[t]
                    (feature_index_set, activation_set) = feature_vector

                    parameters[clique_set_index][true_state_index, feature_index_set] += learning_rate*activation_set
                    parameters[clique_set_index][:, feature_index_set] -= learning_rate*marginal_vector*activation_set 

        elif self.inference_algorithm.id in ['exact inference', 'loopy belief propagation']:

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'): 

                for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                    t = clique.position

                    if t == 0:
                        continue

                    marginal_vector = marginal_vector_set[t]
                    true_state_index = true_state_index_set[t]
                    num_states = marginal_vector.size
                
                    feature_vector = feature_vector_set[t]
                    (feature_index_set, activation_set) = feature_vector

                    parameters[clique_set_index][true_state_index, feature_index_set] += learning_rate*activation_set
                    parameters[clique_set_index][:, feature_index_set] -= learning_rate*marginal_vector*activation_set 

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'): 

                for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                    marginal_vector = marginal_vector_set[clique.position]
                    true_state_index = true_state_index_set[clique.position]
                    num_states = marginal_vector.size
                
                    t_i, t_j = clique.position
                        
                    feature_vector = feature_vector_set[t_j]
                    (feature_index_set, activation_set) = feature_vector

                    parameters[clique_set_index][true_state_index, feature_index_set] += learning_rate*activation_set
                    parameters[clique_set_index][:, feature_index_set] -= learning_rate*marginal_vector*activation_set

            
        return parameters, hyperparameters


