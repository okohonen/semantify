
from cliques import *



class NonStructuredChain(object):
    
    def __init__(self):

        self.id = 'non-structured-chain'

        return


    def get_clique_set_index_set(self, size):

        clique_set_index_set = None

        if size == 'single':
            clique_set_index_set = [0]

        return clique_set_index_set  


    def get_clique_set(self, len_observation, clique_set_index):

        # return 
        clique_set = []
                
        if clique_set_index == 0:

            for t in range(len_observation):

                clique_set.append(Clique('single', (0, t), clique_set_index))                   
                    
        return clique_set



class NonStructuredTwoLevelGrid(object):
    
    def __init__(self):

        self.id = 'nonstructured-two-level-grid'

        return

    def get_clique_set_index_set(self, size):

        if size == 'single':
            clique_set_index_set = [0, 1]
        elif size == 'all':
            clique_set_index_set = [0, 1]

        return clique_set_index_set  


    def get_clique_set(self, len_observation, clique_set_index):

        # return 
        clique_set = []
                
        if clique_set_index == 0: 

            for t in range(len_observation):

                clique_set.append(Clique('single', (0, t), clique_set_index))                   
                    
        elif clique_set_index == 1: 

            for t in range(len_observation):

                clique_set.append(Clique('single', (1, t), clique_set_index))                                     

        return clique_set


class FirstOrderChain(object):
    
    def __init__(self):

        self.id = 'first-order-chain'

        return


    def get_clique_set_index_set(self, size):

        if size == 'single':
            clique_set_index_set = [0]
        elif size == 'double':
            clique_set_index_set = [1]
        elif size == 'all':
            clique_set_index_set = [0, 1]

        return clique_set_index_set  


    def get_sub_clique_set_index_set(self, clique_set_index):
        
        sub_clique_set_index_set = None, None

        if clique_set_index == 1:
            
            sub_clique_set_index_set = (0, 0)

        return sub_clique_set_index_set


    def get_clique_set(self, len_observation, clique_set_index):

        # return 
        clique_set = []
                
        if clique_set_index == 0: # singleton cliques

            for t in range(len_observation):

                clique_set.append(Clique('single', (0, t), clique_set_index))                   
                    
        elif clique_set_index == 1: # doubleton cliques

            for t in range(1, len_observation):

                clique_set.append(Clique('double', ((0, t-1), (0, t)), clique_set_index))                               

        return clique_set

        return clique_set


    def get_dependent_clique_set(self, len_observation, node):

        dependent_clique_set = []

        (l, t) = node

        if t >= 1:
            node_i = (l, t-1)
            node_j = (l, t)
            clique_set_index = 1
            dependent_clique_set.append(Clique('double', (node_i, node_j), clique_set_index))
        if t < len_observation - 1:
            node_i = (l, t)
            node_j = (l, t+1)
            clique_set_index = 1
            dependent_clique_set.append(Clique('double', (node_i, node_j), clique_set_index))

        return dependent_clique_set




class TwoLevelGrid(object):
    
    def __init__(self):

        self.id = 'two-level-grid'

        return


    def get_clique_set_index_set(self, size):

        if size == 'single':
            clique_set_index_set = [0, 1]
        elif size == 'double':
            clique_set_index_set = [2, 3, 4]
        elif size == 'all':
            clique_set_index_set = [0, 1, 2, 3, 4]

        return clique_set_index_set  


    def get_sub_clique_set_index_set(self, clique_set_index):
        
        sub_clique_set_index_set = None

        if clique_set_index == 2:
            
            sub_clique_set_index_set = (0, 1)

        elif clique_set_index == 3:            

            sub_clique_set_index_set = (0, 0)

        elif clique_set_index == 4:
            
            sub_clique_set_index_set = (1, 1)

        return sub_clique_set_index_set


    def get_clique_set(self, len_observation, clique_set_index):

        # return 
        clique_set = []
                
        if clique_set_index == 0: # singleton cliques

            for t in range(len_observation):

                clique_set.append(Clique('single', (0, t), clique_set_index))                   
                    
        elif clique_set_index == 1: # singleton cliques

            for t in range(len_observation):

                clique_set.append(Clique('single', (1, t), clique_set_index))                                     

        elif clique_set_index == 2: # doubleton cliques

            for t in range(0, len_observation):

                clique_set.append(Clique('double', ((0, t), (1, t)), clique_set_index))

        elif clique_set_index == 3: # doubleton cliques

            for t in range(1, len_observation):

                clique_set.append(Clique('double', ((0, t-1), (0, t)), clique_set_index))

        elif clique_set_index == 4: # doubleton cliques

            for t in range(1, len_observation):

                clique_set.append(Clique('double', ((1, t-1), (1, t)), clique_set_index))                               

        return clique_set


    def get_dependent_clique_set(self, len_observation, node):

        dependent_clique_set = []

        (l, t) = node

        # take clique from same time position
        node_i = (0, t)
        node_j = (1, t)        
        clique_set_index = 2
        dependent_clique_set.append(Clique('double', (node_i, node_j), clique_set_index))

        # take cliques from same chain

        if l == 0:
            clique_set_index = 3
        elif l == 1:
            clique_set_index = 4

        if t >= 1:
            node_i = (l, t-1)
            node_j = (l, t)
            dependent_clique_set.append(Clique('double', (node_i, node_j), clique_set_index))
        if t < len_observation - 1:
            node_i = (l, t)
            node_j = (l, t+1)
            dependent_clique_set.append(Clique('double', (node_i, node_j), clique_set_index))

        return dependent_clique_set


    def get_chain_index_set(self, direction, len_observation = None):

        chain_index_set = []

        if direction == 'horizontal':

            chain_index_set = [0, 1]

        elif direction == 'vertical':

            chain_index_set = range(len_observation)

        return chain_index_set




        







