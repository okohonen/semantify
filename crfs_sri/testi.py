

import numpy
import copy


potential_vector_set = {} 
potential_vector_set[((0, 0), (0, 1))] = numpy.array([[0,0,0], [0,0,0], [0,0,0]])
potential_vector_set[((0, 1), (0, 2))] = numpy.array([[0,0,0], [0,0,0], [0,0,0]])
potential_vector_set[((0, 2), (0, 3))] = numpy.array([[0,0,0], [0,0,0], [0,0,0]])
potential_vector_set[((0, 3), (0, 4))] = numpy.array([[0,0,0], [0,0,0], [0,0,0]])

len_observation = len(potential_vector_set)+1
num_states = [3,9]
start = 0
stop = 2


# NUMERICALLY UNSTABLE VERSION

# normalization term logZ

for t in range(1, len_observation):
                                           
    transition = potential_vector_set[((0, t-1), (0, t))]
    transition = numpy.exp(transition)
            
    if t == 1:
        product = transition
    else:
        product = numpy.dot(product, transition)
    
Z = product[start, stop]

# forward

messages = {}

message = numpy.zeros(num_states[0])
message[start] = 1
messages[(-1, 0)] = message

for t in range(1, len_observation):
                                               
    transition = potential_vector_set[((0, t-1), (0, t))]
    transition = numpy.exp(transition)

    message = numpy.dot(messages[(t-2, t-1)], transition)               
#    message = numpy.sum(messages[(t-2, t-1)].reshape(messages[(t-2, t-1)].size, 1) * transition, 0)

    messages[(t-1, t)] = message

# backward

message = numpy.zeros(num_states[0])
message[stop] = 1
messages[(len_observation, len_observation-1)] = message
    
for t in range(len_observation-2, -1, -1):    

    transition = potential_vector_set[((0, t), (0, t+1))]
    transition = numpy.exp(transition)

    message = numpy.dot(transition, messages[(t+2, t+1)])
    messages[(t+1, t)] = message 

# compute marginals

marginal_vector_set = {}

marginal_sum = 0

for t in range(1, len_observation):            

    potential_vector = potential_vector_set[((0, t-1), (0, t))]
    potential_vector = numpy.exp(potential_vector)
    left_message = messages[(t-2, t-1)]
    right_message = messages[(t+1, t)]
    marginal_vector = left_message.reshape(left_message.size, 1) * potential_vector * right_message.reshape(1, right_message.size) / Z
    marginal_vector_set[((0, t-1), (0, t))] = marginal_vector.reshape(marginal_vector.size, 1)

    marginal_sum += numpy.sum(marginal_vector)
            
    verbose = 1
    if verbose:
        print t-1, t
        print "message from left", left_message
        print "potential", potential_vector
        print "message from right", right_message.T
        print "Z", Z
#        print "left*potential", left_message.reshape(left_message.size, 1) * potential_vector
#        print "left*potential*right", left_message.reshape(left_message.size, 1) * potential_vector * right_message.reshape(1, right_message.size)
#        print "potential*right", potential_vector * right_message.reshape(1, right_message.size)
        print "marginal vector", marginal_vector
        print "sum(marginal vector)", numpy.sum(marginal_vector)
        print "total probability so far (should go to 1.0)", marginal_sum
        raw_input("")

exit()




# NUMERICALLY STABLE VERSION

for t in range(1, len_observation):
    
    # normalization term logZ
                                           
    transition = copy.copy(potential_vector_set[((0, t-1), (0, t))])

    normalizer += numpy.max(transition)
    transition -= numpy.max(transition)
    transition = numpy.exp(transition)
            
    if t == 1:
        product = transition
    else:
        product = numpy.dot(product, transition)

    logZ = numpy.log(product[0,1]) + normalizer

    # forward
    
    messages = {}
    normalizers = {}

    message = numpy.zeros(self.state_manager.num_states[0])
    message[self.state_manager.state_sets[0].index('START')] = 1
    normalizer = numpy.log(numpy.max(message))
    normalizers[(-1, 0)] = normalizer
    message /= numpy.max(message)
    messages[(-1, 0)] = message

    for t in range(1, len_observation):
                                               
        transition = potential_vector_set[((0, t-1), (0, t))]
        transition = numpy.exp(transition)

        message = numpy.dot(messages[(t-2, t-1)], transition)               
        normalizer += numpy.log(numpy.max(message))
        normalizers[(t-1, t)] = normalizer
        message /= numpy.max(message)
        messages[(t-1, t)] = message.reshape((1, message.size))

    # backward

    message = numpy.zeros(self.state_manager.num_states[0])
    message[self.state_manager.state_sets[0].index('STOP')] = 1
    normalizer = numpy.log(numpy.max(message))
    normalizers[(len_observation, len_observation-1)] = normalizer
    message /= numpy.max(message)
    messages[(len_observation, len_observation-1)] = message
    
    for t in range(len_observation-2, -1, -1):
                                               
        transition = potential_vector_set[((0, t), (0, t+1))].T
        transition = numpy.exp(transition)

        message = numpy.dot(transition, messages[(t+2, t+1)])
        normalizer += numpy.log(numpy.max(message))
        normalizers[(t+1, t)] = normalizer
        message /= numpy.max(message)               
        messages[(t+1, t)] = message.reshape((message.size, 1))

    # compute marginals

    marginal_vector_set = {}

    marginal_sum = 0

    for t in range(1, len_observation):            

        potential_vector = potential_vector_set[((0, t-1), (0, t))]
        potential_vector = numpy.exp(potential_vector)
        left_message = messages[(t-2, t-1)]
        right_message = messages[(t+1, t)]
        marginal_vector = left_message * potential_vector * right_message * numpy.exp(normalizers[(t-2, t-1)] + normalizers[(t+1, t)] - logZ)
        marginal_vector_set[((0, t-1), (0, t))] = marginal_vector.reshape(marginal_vector.size, 1)

        marginal_sum += numpy.sum(marginal_vector)
            
        verbose = 0
        if verbose:
            print t-1, t
            print "message from left", left_message
            print "potential", potential_vector
            print "message from right", right_message
            print "normalizer forward", normalizers[(t-2, t-1)]
            print "normalizer backward", normalizers[(t+1, t)]
            print "logZ", logZ
            print "exp(normalizers - logZ)", numpy.exp(normalizers[(t-2, t-1)] + normalizers[(t+1, t)] - logZ)
            print "left*potential*right", left_message * potential_vector * right_message
            print "marginal vector", marginal_vector
            print "sum(marginal vector)", numpy.sum(marginal_vector)
            print "total probability so far (should go to 1.0)", marginal_sum
            raw_input("")


exit()






X = numpy.array([[1,2,3],[4,5,6],[7,8,9]])

for i in range(5):

    if i == 0:

        message_transition = X
        
    else:
        
        message_transition = message +X

    print i, message



print "---"



X = numpy.array([[1,2,3],[4,5,6],[7,8,9]])
z = []

for i in range(5):

    z.append(numpy.max(X))
    X2 = copy.copy(X)
    X2 -= numpy.max(X)
    X2 = numpy.exp(X2)
    
    if i == 0:

        Y = X2

    else:

        Y = numpy.dot(Y,X2)

    max_value = numpy.max(message_transition)
    message_transition -= max_value
    message_transition = numpy.exp(message_transition)
    message = numpy.sum(message_transition, 0)

    start_stop = Y[0,2]*numpy.prod(numpy.exp(z))
    print "(start, stop)", start_stop

    start_stop = numpy.log(Y[0,2]) + numpy.sum(z)
    print "log (start, stop)", start_stop








exit()




X = numpy.array([[1,2,3],[4,5,6],[7,8,9]])

for i in range(5):

    if i == 0:

        X2 = numpy.exp(X)
        Y = X2

    else:
        
        X2 = numpy.exp(X)
        Y = numpy.dot(Y,X2)

    print "(start, stop)", Y[0,2]

    print "log (start, stop)", numpy.log(Y[0,2])



print "---"



X = numpy.array([[1,2,3],[4,5,6],[7,8,9]])
z = []

for i in range(5):

    z.append(numpy.max(X))
    X2 = copy.copy(X)
    X2 -= numpy.max(X)
    X2 = numpy.exp(X2)
    
    if i == 0:

        Y = X2

    else:

        Y = numpy.dot(Y,X2)

    start_stop = Y[0,2]*numpy.prod(numpy.exp(z))
    print "(start, stop)", start_stop

    start_stop = numpy.log(Y[0,2]) + numpy.sum(z)
    print "log (start, stop)", start_stop








exit()


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

    
    
