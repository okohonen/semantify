
from parsers import *
import numpy


class StateManager(object):

    # __init__
    def __init__(self, train_file, corpus_id, task_id, graph):
        
        self.parser = TrainFileParser(train_file, corpus_id, task_id)
        self.graph = graph

        self.state_sets, self.num_states = self.process()
        self.tag_dictionary = self.make_tag_dictionary()

        return


    def make_tag_dictionary(self):
        # (Rathnaparkhi, 1996)
        
        # initialize

        tag_dictionary = {}

        self.parser.open()

        # fetch states from training data

        for instance_index in range(self.parser.size):

            observation, len_observation, true_state_set = self.parser.parse(instance_index)

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
                
                for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                    state = true_state_set[clique.position]

                    state_index = self.state_sets[clique_set_index].index(state)

                    l, t = clique.position
                    
                    if observation[t] not in tag_dictionary:
                        
                        tag_dictionary[observation[t]] = [state_index]

                    elif state_index not in tag_dictionary[observation[t]]:

                        tag_dictionary[observation[t]].append(state_index)

        # sort

        for key, value in tag_dictionary.items():

            tag_dictionary[key] = sorted(value)

        # close parser

        self.parser.close()

        return tag_dictionary
        



class StructuredStateManager(StateManager):

    # __init__
    def __init__(self, train_file, corpus_id, task_id, graph):

        super(StructuredStateManager, self).__init__(train_file, corpus_id, task_id, graph)
        self.transition_matrix_set = self.make_transition_matrix_set()

        return


    def process(self):

        # initialize

        self.parser.open()

        state_sets = []
        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
            state_sets.append(['START', 'STOP'])
        for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'):
            state_sets.append([])

        # fetch states from training data

        for instance_index in range(self.parser.size):

            observation, len_observation, true_state_set = self.parser.parse(instance_index)

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
                
                for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                    state = true_state_set[clique.position]

                    if state not in state_sets[clique_set_index]:
                        state_sets[clique_set_index].append(state)

        # make state transitions

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'):
            (clique_set_index_i, clique_set_index_j) = self.graph.get_sub_clique_set_index_set(clique_set_index)
            for state_i in state_sets[clique_set_index_i]:
                for state_j in state_sets[clique_set_index_j]:
                    state_sets[clique_set_index].append((state_i, state_j))

        # number of states

        num_states = []
      
        for clique_set_index in self.graph.get_clique_set_index_set(size = 'all'):
            num_states.append(len(state_sets[clique_set_index]))

        # close parser

        self.parser.close()

        return state_sets, num_states


    def convert_state_set_to_state_index_set(self, state_set, len_observation): 

        if state_set == None:
            
            state_index_set = None

        else:

            state_index_set = {} 

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'all'):
            
                for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                    if clique.size == 'single':
                        
                        state = state_set[clique.position]
                
                    else:

                        (node_i, node_j) = clique.position
                        
                        state = (state_set[node_i], state_set[node_j])

                    try:
                        
                        state_index_set[clique.position] = self.state_sets[clique_set_index].index(state)

                    except ValueError:

                        state_index_set[clique.position] = -1                    

        return state_index_set


    def convert_state_index_set_to_state_set(self, state_index_set, len_observation): 

        state_set = {} 

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'all'): 

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                try:

                    state_index = state_index_set[clique.position]

                except:

                    state_index = -1

                state_set[clique.position] = self.state_sets[clique_set_index][state_index]

        return state_set 


    def make_transition_matrix_set(self):

        transition_matrix_set = []

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):

            transition_matrix_set.append(None)

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'):
        
            state_set_cardinality = self.num_states[clique_set_index]

            clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)            
            state_set_cardinality_i = self.num_states[clique_set_index_i]
            state_set_cardinality_j = self.num_states[clique_set_index_j]
            
            transition_matrix_set.append(numpy.array(range(state_set_cardinality)).reshape(state_set_cardinality_i, state_set_cardinality_j))

        return transition_matrix_set

    




class NonStructuredStateManager(StateManager):

    # __init__
    def __init__(self, train_file, corpus_id, task_id, graph):

        super(NonStructuredStateManager, self).__init__(train_file, corpus_id, task_id, graph)
        
        return


    def process(self):

        # initialize

        self.parser.open()

        state_sets = []
        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
            state_sets.append(['START', 'STOP'])

        # fetch states from training data

        for instance_index in range(self.parser.size):

            observation, len_observation, true_state_set = self.parser.parse(instance_index)

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
                
                for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                    state = true_state_set[clique.position]

                    if state not in state_sets[clique_set_index]:
                        state_sets[clique_set_index].append(state)

        # number of states

        num_states = []
      
        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
            num_states.append(len(state_sets[clique_set_index]))

        # close parser

        self.parser.close()

        return state_sets, num_states


    def convert_state_set_to_state_index_set(self, state_set, len_observation): 

        if state_set == None:
            
            state_index_set = None

        else:

            state_index_set = {} 

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
            
                for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                    if clique.size == 'single':
                        
                        state = state_set[clique.position]
                
                    else:

                        (node_i, node_j) = clique.position
                        
                        state = (state_set[node_i], state_set[node_j])

                    try:
                        
                        state_index_set[clique.position] = self.state_sets[clique_set_index].index(state)

                    except ValueError:

                        state_index_set[clique.position] = -1                    

        return state_index_set


    def convert_state_index_set_to_state_set(self, state_index_set, len_observation): 

        state_set = {} 

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'): 

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                try:

                    state_index = state_index_set[clique.position]

                except:

                    state_index = -1

                state_set[clique.position] = self.state_sets[clique_set_index][state_index]

        return state_set 

