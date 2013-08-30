
from potential_functions import *

import numpy
import copy

# fixme
import numpy.random


class InferenceAlgorithm(object):

    def __init__(self, graph, state_manager):

        self.graph = graph
        self.state_manager = state_manager
        
        return





class NonStructuredInference(InferenceAlgorithm):


    def __init__(self, graph, state_manager):

        super(NonStructuredInference, self).__init__(graph, state_manager)

        self.id = 'nonstructured inference'

        self.potential_function = NonStructuredPotentialFunction(graph, state_manager)

        return


    def compute_marginal_vector_set(self, parameters, feature_vector_set, len_observation, observation = None):

        potential_vector_set = self.potential_function.compute_potential_vector_set(parameters, feature_vector_set, len_observation)
        
        marginal_vector_set = {}

        logZ = 0

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'): 

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                potential_vector = potential_vector_set[clique.position]
                potential_vector -= numpy.max(potential_vector)
                potential_vector = numpy.exp(potential_vector)
                marginal_vector_set[clique.position] = potential_vector / numpy.sum(potential_vector)

        return marginal_vector_set


    def compute_map_state_index_set(self, parameters, feature_vector_set, len_observation, observation = None):

        potential_vector_set = self.potential_function.compute_potential_vector_set(parameters, feature_vector_set, len_observation, observation)
        
        map_state_index_set = {}

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'): 

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                map_state_index_set[clique.position] = numpy.argmax(potential_vector_set[clique.position])

        map_state_set = self.state_manager.convert_state_index_set_to_state_set(map_state_index_set, len_observation)

        return map_state_index_set, map_state_set




class ExactInference(InferenceAlgorithm):
    # exact inference for a first order chain

    def __init__(self, graph, state_manager):

        super(ExactInference, self).__init__(graph, state_manager)

        self.id = 'exact inference'

        self.potential_function = StructuredPotentialFunction(graph, state_manager)

        return


    def compute_marginal_vector_set(self, parameters, feature_vector_set, len_observation):
        
        potential_vector_set = self.potential_function.compute_potential_vector_set(parameters, feature_vector_set, len_observation)
        
        for key, value in potential_vector_set.items():
            potential_vector_set[key] = numpy.exp(value)

        # forward

        messages = {}
        normalizers = {}

        message = numpy.zeros(self.state_manager.num_states[0])
        message[self.state_manager.state_sets[0].index('START')] = 1
        messages[(-1, 0)] = message

        for t in range(1, len_observation):
                                               
            transition = potential_vector_set[((0, t-1), (0, t))]

            message = numpy.dot(messages[(t-2, t-1)], transition)               
            message /= numpy.max(message)
            messages[(t-1, t)] = message

        # backward

        message = numpy.zeros(self.state_manager.num_states[0])
        message[self.state_manager.state_sets[0].index('STOP')] = 1
        messages[(len_observation, len_observation-1)] = message
    
        for t in range(len_observation-2, -1, -1):
                                               
            transition = potential_vector_set[((0, t), (0, t+1))]

            message = numpy.dot(transition, messages[(t+2, t+1)])
            message /= numpy.max(message)               
            messages[(t+1, t)] = message

        # compute marginals

        marginal_vector_set = {}

        for t in range(0, len_observation):            

            # single

            left_message = messages[(t-1, t)]
            right_message = messages[(t+1, t)]
            marginal_vector = left_message * right_message
            marginal_vector /= numpy.sum(marginal_vector)
            marginal_vector_set[(0, t)] = marginal_vector.reshape(marginal_vector.size, 1)

        for t in range(1, len_observation):            

            # double

            potential_vector = potential_vector_set[((0, t-1), (0, t))]
            left_message = messages[(t-2, t-1)]
            right_message = messages[(t+1, t)]
            marginal_vector = left_message.reshape(left_message.size, 1) * potential_vector * right_message.reshape(1, right_message.size)
            marginal_vector /= numpy.sum(marginal_vector)
            marginal_vector_set[((0, t-1), (0, t))] = marginal_vector.reshape(marginal_vector.size, 1)

        return marginal_vector_set


    def compute_map_state_index_set(self, parameters, feature_vector_set, len_observation, observation = None):
        
        potential_vector_set = self.potential_function.compute_potential_vector_set(parameters, feature_vector_set, len_observation, observation)

        map_state_index_set = {}

        backtrack_pointers = -1*numpy.ones((len_observation, self.state_manager.num_states[0]))
                                           
        a = None
        
        for t_j in range(1, len_observation):
                                               
            t_i = t_j - 1
            ab = potential_vector_set[((0, t_i), (0, t_j))]
            if a != None:
                a_ab = a.reshape(a.size, 1) + ab # broadcast
            else:
                a_ab = ab
            backtrack_pointers[t_j, :] = numpy.argmax(a_ab, 0)
            a = numpy.max(a_ab, 0)

        map_state_index_set[(0, t_j)] = int(numpy.argmax(a))

        # backward
                
        for t_j in range(len_observation-1, 0, -1):
                                          
            t_i = t_j - 1

            map_j = map_state_index_set[(0, t_j)] # t_j already has likeliest state
            map_i = int(backtrack_pointers[t_j, map_j])
            map_state_index_set[(0, t_i)] = map_i
            map_state_index_set[((0, t_i), (0, t_j))] = int(map_i*self.state_manager.num_states[0] + map_j)

        map_state_set = self.state_manager.convert_state_index_set_to_state_set(map_state_index_set, len_observation)

        return map_state_index_set, map_state_set


