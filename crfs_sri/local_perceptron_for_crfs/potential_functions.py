
import numpy




class NonStructuredPotentialFunction(object):


    def __init__(self, graph, state_manager):

        self.graph = graph        
        self.state_manager = state_manager

        return


    def compute_potential_vector_set(self, parameters, feature_vector_set, len_observation, observation = None):

        # return this
        potential_vector_set = {}

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
                       
            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                l_j, t_j = clique.position

                feature_vector = feature_vector_set[t_j]

                potential_vector_set[clique.position] = self.compute_potential_vector(parameters, clique_set_index, feature_vector)
                
        return potential_vector_set


    def compute_potential_vector(self, parameters, clique_set_index, feature_vector):

        feature_index_set, activation_set = feature_vector

        potential_vector = numpy.sum(parameters[clique_set_index][:, feature_index_set]*activation_set, 1)

        return potential_vector



class StructuredPotentialFunction(object):


    def __init__(self, graph, state_manager):

        self.graph = graph        
        self.state_manager = state_manager

        return


    def compute_potential_vector_set(self, parameters, feature_vector_set, len_observation, observation = None):

        # return this
        potential_vector_set = {}

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
                       
            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                l_j, t_j = clique.position

                feature_vector = feature_vector_set[t_j]

                potential_vector_set[clique.position] = self.compute_potential_vector(parameters, clique_set_index, feature_vector)

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'):
                       
            clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):
                
                node_i, node_j = clique.position
                l_i, t_i = node_i
                l_j, t_j = node_j
                
                if observation != None:

                    state_index_set = self.state_manager.tag_dictionary.get(observation[t_j], -1)

                    if state_index_set == -1:

                        potential_vector = self.compute_potential_vector(parameters, clique_set_index, feature_vector_set[t_j])
                        potential_vector = potential_vector.reshape((self.state_manager.num_states[clique_set_index_i], self.state_manager.num_states[clique_set_index_j]))
                    
                        potential_vector_j = potential_vector_set[node_j] # self.compute_potential_vector(parameters, clique_set_index_j, feature_vector_set[t_j])

                        potential_vector_set[clique.position] = potential_vector+potential_vector_j                        

                    else:
                    
                        p = self.compute_potential_vector(parameters, clique_set_index, feature_vector_set[t_j])
                        p = p.reshape((self.state_manager.num_states[clique_set_index_i], self.state_manager.num_states[clique_set_index_j]))
                        potential_vector = numpy.zeros_like(p)
                        potential_vector[:, state_index_set] = p[:, state_index_set]

                        p = potential_vector_set[node_j] # self.compute_potential_vector(parameters, clique_set_index_j, feature_vector_set[t_j])
                        potential_vector_j = numpy.zeros_like(p)
                        potential_vector_j[state_index_set] = p[state_index_set]

                        potential_vector_set[clique.position] = potential_vector+potential_vector_j

                else:

                    potential_vector = self.compute_potential_vector(parameters, clique_set_index, feature_vector_set[t_j])
                    potential_vector = potential_vector.reshape((self.state_manager.num_states[clique_set_index_i], self.state_manager.num_states[clique_set_index_j]))
                    
                    potential_vector_j = potential_vector_set[node_j] # self.compute_potential_vector(parameters, clique_set_index_j, feature_vector_set[t_j])

                    potential_vector_set[clique.position] = potential_vector+potential_vector_j

        return potential_vector_set


    def compute_potential_vector(self, parameters, clique_set_index, feature_vector):

        (feature_index_set, activation_set) = feature_vector

        potential_vector = numpy.sum(parameters[clique_set_index][:, feature_index_set]*activation_set, 1)

        return potential_vector



class PseudoPotentialFunction(object):


    def __init__(self, graph, state_manager, pseudo_mask_matrix_set):

        self.graph = graph        
        self.state_manager = state_manager

        self.pseudo_mask_matrix_set = pseudo_mask_matrix_set 

        return


    def compute_potential_vector_set(self, parameters, feature_vector_set, len_observation, true_state_index_set):

        # return this
        potential_vector_set = {}

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
                       
            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                l_j, t_j = clique.position

                feature_vector = feature_vector_set[t_j]

                potential_vector_set[clique.position] = self.compute_potential_vector(parameters, clique_set_index, feature_vector)
                
        for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'):
                       
            clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):
                
                (node_i, node_j) = clique.position
                (l_i, t_i) = node_i
                (l_j, t_j) = node_j

                # node i is free
                row_index_set = self.pseudo_mask_matrix_set[clique_set_index][:, true_state_index_set[node_j]]
                potential_vector = self.compute_potential_vector(parameters, clique_set_index, feature_vector_set[t_j], row_index_set)
                potential_vector += self.compute_potential(parameters, clique_set_index, feature_vector_set[t_j], true_state_index_set[node_j])
                potential_vector_set[(clique.position, node_i)] = potential_vector
                        
                # node j is free
                row_index_set = self.pseudo_mask_matrix_set[clique_set_index][true_state_index_set[node_i], :]
                potential_vector = self.compute_potential_vector(parameters, clique_set_index, feature_vector_set[t_j], row_index_set)
                potential_vector += potential_vector_set[node_j]
                potential_vector_set[(clique.position, node_j)] = potential_vector

        return potential_vector_set


    def compute_potential(self, parameters, clique_set_index, feature_vector, state_index):

        feature_index_set, activation_set = feature_vector

        potential = numpy.sum(parameters[clique_set_index][state_index, feature_index_set])

        return potential
    

    def compute_potential_vector(self, parameters, clique_set_index, feature_vector, row_index_set = None):

        (feature_index_set, activation_set) = feature_vector

        if row_index_set == None:
            
            potential_vector = numpy.sum(parameters[clique_set_index][:, feature_index_set]*activation_set, 1)

        else:

            potential_vector = numpy.sum(parameters[clique_set_index][numpy.ix_(row_index_set, feature_index_set)]*activation_set, 1)

        return potential_vector


    def prepare_pseudo_mask_matrix_set(self, state_manager):

        pseudo_mask_matrix_set = []

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):

            pseudo_mask_matrix_set.append(None)

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'):
        
            state_set_cardinality = state_manager.num_states[clique_set_index]

            clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)            
            state_set_cardinality_i = state_manager.num_states[clique_set_index_i]
            state_set_cardinality_j = state_manager.num_states[clique_set_index_j]
            
            pseudo_mask_matrix_set.append(numpy.array(range(state_set_cardinality)).reshape(state_set_cardinality_i, state_set_cardinality_j))

        return pseudo_mask_matrix_set






    



