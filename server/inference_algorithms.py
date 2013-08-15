
from potential_functions import *

import numpy
import copy
import time # fixme

class InferenceAlgorithm(object):

    def __init__(self, graph, state_manager):

        self.graph = graph
        self.state_manager = state_manager
        
        return

    def get_id(self):
        return self.id



class NonStructuredInference(InferenceAlgorithm):


    def __init__(self, graph, state_manager):

        super(NonStructuredInference, self).__init__(graph, state_manager)

        self.id = 'non-structured inference'

        self.potential_function = NonStructuredPotentialFunction(graph, state_manager)

        return


    def compute_marginal_vector_set(self, parameters, feature_vector_set, len_observation):

        potential_vector_set = self.potential_function.compute_potential_vector_set(parameters, feature_vector_set, len_observation)
        
        marginal_vector_set = {}

        for t in range(len_observation):

            potential_vector = potential_vector_set[t]
            potential_vector -= numpy.max(potential_vector)
            potential_vector = numpy.exp(potential_vector)
            marginal_vector_set[t] = potential_vector.reshape(potential_vector.size, 1)/numpy.sum(potential_vector)

        return marginal_vector_set


    def compute_map_state_index_set(self, parameters, feature_vector_set, len_observation):

        potential_vector_set = self.potential_function.compute_potential_vector_set(parameters, feature_vector_set, len_observation)
        
        map_state_index_set = {}

        for t in range(len_observation):

                map_state_index_set[t] = numpy.argmax(potential_vector_set[t])

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
                                               
            transition = potential_vector_set[(t-1, t)]

            message = numpy.dot(messages[(t-2, t-1)], transition)               
            message /= numpy.max(message)
            messages[(t-1, t)] = message

        # backward

        message = numpy.zeros(self.state_manager.num_states[0])
        message[self.state_manager.state_sets[0].index('STOP')] = 1
        messages[(len_observation, len_observation-1)] = message
    
        for t in range(len_observation-2, -1, -1):
                                               
            transition = potential_vector_set[(t, t+1)]

            message = numpy.dot(transition, messages[(t+2, t+1)])
            message /= numpy.max(message)               
            messages[(t+1, t)] = message

        # compute marginals

        marginal_vector_set = {}

        for t in range(1, len_observation):            

            # single node

            left_message = messages[(t-1, t)]
            right_message = messages[(t+1, t)]
            marginal_vector = left_message*right_message
            marginal_vector /= numpy.sum(marginal_vector)
            marginal_vector_set[t] = marginal_vector.reshape(marginal_vector.size, 1)

            # double node

            potential_vector = potential_vector_set[(t-1, t)]
            left_message = messages[(t-2, t-1)]
            right_message = messages[(t+1, t)]
            marginal_vector = left_message.reshape(left_message.size, 1) * potential_vector * right_message.reshape(1, right_message.size)
            marginal_vector /= numpy.sum(marginal_vector)
            marginal_vector_set[(t-1, t)] = marginal_vector.reshape(marginal_vector.size, 1)

        return marginal_vector_set


    def compute_map_state_index_set(self, parameters, feature_vector_set, len_observation):
        
        potential_vector_set = self.potential_function.compute_potential_vector_set(parameters, feature_vector_set, len_observation)

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
                                          
            map_j = map_state_index_set[t] # t_j already has likeliest state
            map_i = int(backtrack_pointers[t, map_j])
            map_state_index_set[t-1] = map_i
            map_state_index_set[(t-1, t)] = int(map_i*self.state_manager.num_states[0] + map_j)

        map_state_set = self.state_manager.convert_state_index_set_to_state_set(map_state_index_set, len_observation)

        return map_state_index_set, map_state_set




class MarginalMAPInference(InferenceAlgorithm):
    # marginal MAP inference for a first order chain

    def __init__(self, graph, state_manager):

        super(ExactInference, self).__init__(graph, state_manager)

        self.id = 'exact inference'

        self.potential_function = StructuredPotentialFunction(graph, state_manager)

        return


    def compute_map_state_index_set(self, parameters, feature_vector_set, len_observation):
        
        potential_vector_set = self.potential_function.compute_potential_vector_set(parameters, feature_vector_set, len_observation)
        
        for key, value in potential_vector_set.items():
            potential_vector_set[key] = numpy.exp(value)

        # forward

        messages = {}

        message = numpy.zeros(self.state_manager.num_states[0])
        message[self.state_manager.state_sets[0].index('START')] = 1
        messages[(-1, 0)] = message

        for t in range(1, len_observation):
                                               
            transition = potential_vector_set[(t-1, t)]

            message = numpy.dot(messages[(t-2, t-1)], transition)               
            message /= numpy.max(message)
            messages[(t-1, t)] = message

        # backward

        message = numpy.zeros(self.state_manager.num_states[0])
        message[self.state_manager.state_sets[0].index('STOP')] = 1
        messages[(len_observation, len_observation-1)] = message
    
        for t in range(len_observation-2, -1, -1):
                                               
            transition = potential_vector_set[(t, t+1)]

            message = numpy.dot(transition, messages[(t+2, t+1)])
            message /= numpy.max(message)               
            messages[(t+1, t)] = message

        # compute map state index set

        map_state_index_set = {}

        for t in range(len_observation):            

            # single node

            left_message = messages[(t-1, t)]
            right_message = messages[(t+1, t)]
            map_state_index_set[t] = numpy.argmax(left_message*right_message)

        for t in range(1, len_observation):            

            # double node

#            map_i = map_state_index_set[t-1]
#            map_j = map_state_index_set[t]
#            map_state_index_set[(t-1, t)] = int(map_i*self.state_manager.num_states[0] + map_j)

            potential_vector = potential_vector_set[(t-1, t)]
            left_message = messages[(t-2, t-1)]
            right_message = messages[(t+1, t)]
            map_state_index_set[(t-1, t)] = numpy.argmax(left_message.reshape(left_message.size, 1) * potential_vector * right_message.reshape(1, right_message.size))
            
        map_state_set = self.state_manager.convert_state_index_set_to_state_set(map_state_index_set, len_observation)

        return map_state_index_set, map_state_set




class LoopyBeliefPropagation(InferenceAlgorithm):
    # loopy belief propagation (Yedidia, 2003)

    def __init__(self, graph, state_manager):

        super(LoopyBeliefPropagation, self).__init__(graph, state_manager)

        self.id = 'loopy belief propagation'

        self.potential_function = StructuredPotentialFunction(graph, state_manager)

        return


    def compute_marginal_vector_set(self, parameters, feature_vector_set, len_observation):

        self.map_inference = False

        potential_vector_set = self.potential_function.compute_potential_vector_set(parameters, feature_vector_set, len_observation)

        for key, value in potential_vector_set.items():

            potential_vector_set[key] = numpy.exp(value)

        initial_messages, message_keys = self.initialize_messages(len_observation)
        converged_messages = self.pass_messages(potential_vector_set, initial_messages, message_keys, len_observation)
        marginal_vector_set = self.get_marginal_vector_set(potential_vector_set, converged_messages, message_keys, len_observation)

        return marginal_vector_set


    def compute_map_state_index_set(self, parameters, feature_vector_set, len_observation):

        self.map_inference = True

        potential_vector_set = self.potential_function.compute_potential_vector_set(parameters, feature_vector_set, len_observation)

        for key, value in potential_vector_set.items():

            potential_vector_set[key] = numpy.exp(value)

        initial_messages, message_keys = self.initialize_messages(len_observation)
        converged_messages = self.pass_messages(potential_vector_set, initial_messages, message_keys, len_observation)
        map_state_index_set = self.get_map_state_index_set(potential_vector_set, converged_messages, message_keys, len_observation)
        map_state_set = self.state_manager.convert_state_index_set_to_state_set(map_state_index_set, len_observation)

        return map_state_index_set, map_state_set


    def initialize_messages(self, len_observation):
        
        # return this
        messages = {}
        message_keys = {'forward' : [], 'backward': []} 

        # initialize from nodes

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                node_i = clique.position
                messages[node_i] = {}
                        
        for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'):

            clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                (node_i, node_j) = clique.position

                # forward

                message_keys['forward'].append((node_i, node_j))
                messages[node_i][node_j] = numpy.ones(self.state_manager.num_states[clique_set_index_j])/self.state_manager.num_states[clique_set_index_j]

                # backward

                message_keys['backward'].insert(0, (node_j, node_i))
                messages[node_j][node_i] = numpy.ones(self.state_manager.num_states[clique_set_index_i])/self.state_manager.num_states[clique_set_index_i]

#        for key, value in messages.items():
#            print key, value

        return messages, message_keys


    def pass_messages(self, potential_vector_set, messages, message_keys, len_observation):

        message_change_threshold = 10**-2
        max_num_iterations = 25
        iteration_index = 0 # number of times node has sent and received message to and from all neighbors
        
        while(1):

            converged = True
            
            for flow_direction in ['forward', 'backward']:
                
                for message_key in message_keys[flow_direction]:

                    (node_i, node_j) = message_key

                    old_message = messages[node_i][node_j]

                    updated_message = self.update_message(potential_vector_set, message_key, messages, flow_direction)
                    
                    messages[node_i][node_j] = updated_message

                    if converged and numpy.max(numpy.abs(1-(updated_message/old_message))) > message_change_threshold:
#                        print numpy.max(numpy.abs(1-old_message/updated_message))
                        converged = False

            iteration_index += 1

            if converged or iteration_index == max_num_iterations:
#                print "convergence:", iteration_index
                break

        return messages


    def update_message(self, potential_vector_set, message_key, messages, flow_direction):
        # update message from node i to node j
        # note: (Yedidia, 2002) equation (14)

        (node_i, node_j) = message_key

        if flow_direction == 'forward':
            potential_vector_ij = potential_vector_set[(node_i, node_j)]
        else:
            potential_vector_ij = potential_vector_set[(node_j, node_i)].T

        if self.map_inference:
        
            incoming_message_product_i = self.combine_incoming_messages(node_i, node_j, messages)
            incoming_message_product_i = incoming_message_product_i.reshape(incoming_message_product_i.size, 1)
            updated_message = numpy.max(incoming_message_product_i * potential_vector_ij, 0) # broadcast
            updated_message /= numpy.sum(updated_message) # normalize

        else:

            incoming_message_product_i = self.combine_incoming_messages(node_i, node_j, messages)
            incoming_message_product_i = incoming_message_product_i.reshape(incoming_message_product_i.size, 1)
            updated_message = numpy.sum(incoming_message_product_i * potential_vector_ij, 0) # broadcast
            updated_message /= numpy.sum(updated_message) # normalize

        return updated_message


    def combine_incoming_messages(self, node_i, node_j, messages):
        # sum/multiply incoming messages to node i skipping node j

        incoming_message_product = None

        for neighbor in messages[node_i]:

            if neighbor != node_j: # skip node_j; see compute_updated_message()

                if incoming_message_product == None:

                    incoming_message_product = copy.copy(messages[neighbor][node_i])

                else:

                    incoming_message_product *= messages[neighbor][node_i]

        return incoming_message_product


    def get_marginal_vector_set(self, potential_vector_set, converged_messages, message_keys, len_observation):

        marginal_vector_set = {}

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                incoming_message_product = self.combine_incoming_messages(clique.position, None, converged_messages)

                marginal_vector = incoming_message_product/numpy.sum(incoming_message_product)

                marginal_vector_set[clique.position] = marginal_vector.reshape(marginal_vector.size, 1)

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'):

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):
                   
                (node_i, node_j) = clique.position

                potential_vector_ij = potential_vector_set[(node_i, node_j)]
            
                incoming_message_product_i = self.combine_incoming_messages(node_i, node_j, converged_messages)
                incoming_message_product_i = incoming_message_product_i.reshape(incoming_message_product_i.size, 1)
                incoming_message_product_j = self.combine_incoming_messages(node_j, node_i, converged_messages)
                incoming_message_product_j = incoming_message_product_j.reshape(1, incoming_message_product_j.size)

                marginal_vector = incoming_message_product_i * potential_vector_ij * incoming_message_product_j
                marginal_vector/numpy.sum(marginal_vector)
                marginal_vector_set[clique.position] = marginal_vector.reshape(marginal_vector.size, 1)
                
        return marginal_vector_set


    def get_map_state_index_set(self, potential_vector_set, converged_messages, message_keys, len_observation):

        map_state_index_set = {}

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                incoming_message_product = self.combine_incoming_messages(clique.position, None, converged_messages)

                map_state_index_set[clique.position] = numpy.argmax(incoming_message_product)

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'):

            clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):
                   
                (node_i, node_j) = clique.position
                
                potential_vector_ij = potential_vector_set[(node_i, node_j)]
            
                incoming_message_product_i = self.combine_incoming_messages(node_i, node_j, converged_messages)
                incoming_message_product_i = incoming_message_product_i.reshape(incoming_message_product_i.size, 1)
                incoming_message_product_j = self.combine_incoming_messages(node_j, node_i, converged_messages)
                incoming_message_product_j = incoming_message_product_j.reshape(1, incoming_message_product_j.size)

                map_state_index_set[clique.position] = numpy.argmax(incoming_message_product_i * potential_vector_ij * incoming_message_product_j)

#        for key, value in map_state_index_set.items():
#            print key, value
#        raw_input("")

        return map_state_index_set


class FactorAsPieceInference(InferenceAlgorithm):

    def __init__(self, graph, state_manager):

        super(FactorAsPieceInference, self).__init__(graph, state_manager)

        self.id = 'piecewise (factor-as-piece) inference'

        self.potential_function = StructuredPotentialFunction(graph, state_manager)

        return


    def compute_marginal_vector_set(self, parameters, feature_vector_set, len_observation):

        potential_vector_set = self.potential_function.compute_potential_vector_set(parameters, feature_vector_set, len_observation)
        
        marginal_vector_set = {}

        logZ = 0

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'): 

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                potential_vector = potential_vector_set[clique.position]
                potential_vector -= numpy.max(potential_vector)
                potential_vector = numpy.exp(potential_vector)
                Z = numpy.sum(potential_vector)
                marginal_vector_set[clique.position] = potential_vector/Z
                logZ += numpy.log(Z)

        return marginal_vector_set, logZ


    def compute_map_state_index_set(self, parameters, feature_vector_set, len_observation):

        potential_vector_set = self.potential_function.compute_potential_vector_set(parameters, feature_vector_set, len_observation)
        
        map_state_index_set = {}

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'): 

            clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                map_state_index = numpy.argmax(potential_vector_set[clique.position])

                map_state_index_set[clique.position] = map_state_index

                map_state_index_j = map_state_index % self.state_manager.num_states[clique_set_index_j]
                
                t_i, t_j = clique.position

                map_state_index_set[(t_j, clique.position)] = map_state_index_j 

        map_state_set = None # this inference is not used at decoding stage

        return map_state_index_set, map_state_set







