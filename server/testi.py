

import numpy

def compute_potential_vector(parameters, feature_vector, num_states, row_index_set):

    potential_vector = []
       
    (feature_index_set, activation_set) = feature_vector

    for state_index in range(num_states):

        potential_vector.append(0)
           
        if state_index in row_index_set:

            for index in range(len(feature_index_set)):

                potential_vector[state_index] += parameters[state_index].get(feature_index_set[index], 0)*activation_set[index]

    return potential_vector


if __name__ == "__main__":

    num_states = 3 # kolme tilaa (esim. substantiivi, adjektiivi, verbi)

    parameters = []
    parameters.append({1: 1, 5 : 10, 10 : 100}) # substantiivia vastaa kolme nollasta poikkeavaa parametria
    parameters.append({2: 1, 3 : 10}) # adjektiivia vastaa kais nollasta poikkeavaa parametria
    parameters.append({4: 1}) # verbi vastaa yksi nollasta poikkeavaa parametri
        
    feature_vector = ([1, 5], [0.5, 1.0]) # kaks aktivoitunutta featurea (esim. bias ja sana on 'auto') aktivaatioilla 0.5 ja 1.0

    row_index_set = [0, 2] # skippaa adjektiivi koska sana voi olla vaan substantiivi tai verbi

    potential_vector = numpy.array(compute_potential_vector(parameters, feature_vector, num_states, row_index_set))

    print potential_vector

    
    
