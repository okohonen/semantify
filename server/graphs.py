
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

                clique_set.append(Clique('single', t, clique_set_index))                   
                    
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

                clique_set.append(Clique('single', t, clique_set_index))                   
                    
        elif clique_set_index == 1: # doubleton cliques

            for t in range(1, len_observation):

                clique_set.append(Clique('double', (t-1, t), clique_set_index))                               

        return clique_set

        return clique_set



class SecondOrderChain(object):
    
    def __init__(self):

        self.id = 'second-order-chain'

        return


    def get_clique_set_index_set(self, size):

        if size == 'single':
            clique_set_index_set = [0]
        elif size == 'double':
            clique_set_index_set = [1, 2]
        elif size == 'all':
            clique_set_index_set = [0, 1, 2]

        return clique_set_index_set  


    def get_sub_clique_set_index_set(self, clique_set_index):
        
        sub_clique_set_index_set = None, None

        if clique_set_index == 1:
            
            sub_clique_set_index_set = (0, 0)

        elif clique_set_index == 2:
            
            sub_clique_set_index_set = (0, 0)

        return sub_clique_set_index_set


    def get_clique_set(self, len_observation, clique_set_index):

        # return 
        clique_set = []
                
        if clique_set_index == 0: # singleton cliques

            for t in range(len_observation):

                clique_set.append(Clique('single', t, clique_set_index))                   
                    
        elif clique_set_index == 1: # doubleton cliques

            for t in range(1, len_observation):

                clique_set.append(Clique('double', (t-1, t), clique_set_index))                               

        elif clique_set_index == 2: # doubleton cliques

            for t in range(2, len_observation):

                clique_set.append(Clique('double', (t-2, t), clique_set_index))                               

        return clique_set






