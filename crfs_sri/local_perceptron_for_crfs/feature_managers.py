
import re
import numpy

from parsers import * 


class FeatureManager(object):

    # __init__
    def __init__(self, train_file, corpus_id, task_id, graph, delta):
        
        self.parser = TrainFileParser(train_file, corpus_id, task_id)
        self.corpus_id = corpus_id
        self.task_id = task_id
        self.graph = graph

        self.delta = delta # word identity context window: t-delta, .., t+delta

        if corpus_id in ['conll2000', 'wsj', 'conll1999']:

            self.reg_exps = self.compile_regexps('./regexps/syntax.re')

        elif corpus_id in ['geniatb']:

            self.reg_exps = self.compile_regexps('./regexps/genia.re')

        self.features, self.num_features = self.process()

        return


    def process(self):
        
        self.parser.open()

        features = {'BIAS': 0}

        for instance_index in range(self.parser.size):

            observation, len_observation, state_set = self.parser.parse(instance_index)

            feature_sets = self.extract_observation_feature_sets(observation, len_observation)
            
            for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
                
                for clique in self.graph.get_clique_set(len(observation), clique_set_index):

                    (l_j, t_j) = clique.position

                    # add feature 
                    for (feature, value) in feature_sets[t_j]:
                        if features.get(feature, -1) == -1:
                            features[feature] = len(features)

        self.parser.close()

        return features, len(features)


    def make_feature_vector_set(self, observation, len_observation):

        feature_vector_set = {}

        feature_sets = self.extract_observation_feature_sets(observation, len_observation)

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):

            for clique in self.graph.get_clique_set(len(observation), clique_set_index):

                (l_j, t_j) = clique.position

                feature_set = feature_sets[t_j]

                feature_index_set = []
                activation_set = []
                for feature, activation in feature_set:

                    feature_index = self.features.get(feature, -1)

                    if feature_index > -1:

                        feature_index_set.append(feature_index)
                        activation_set.append(activation) 
                
                feature_vector = (numpy.array(feature_index_set, dtype=numpy.int32), numpy.array(activation_set, dtype=numpy.int32))

                feature_vector_set[t_j] = feature_vector

        return feature_vector_set


    def compile_regexps(self, regexp_file):

        # return this
        reg_exps = []

        for pattern in file(regexp_file): 
            pattern = pattern.split('#')[0].strip() # discard comment after #
            if pattern != '':
                reg_exps.append((pattern, re.compile(pattern)))

        return reg_exps


    def extract_observation_feature_sets(self, observation, len_observation):

        # return features sets in dictionary
        feature_sets = []
        
        feature_sets.append([('BIAS', 1), ('word identity t <s>', 1)])

        for t in range(1, len_observation-1):

            feature_sets.append([])

            # bias
            feature_sets[t].append(('BIAS', 1))

            # bias
            feature_sets[t].append(('BIAS', 1))

            if self.corpus_id in ['synthesized']:

                # word identity and POS tag

                feature_sets[t].append(('word identity t: %s' % observation[t], 1))

            elif self.corpus_id in ['conll1999', 'conll2000']:

                # word identity and POS tag

                word, pos = observation[t].split()
                feature_sets[t].append(('word identity t: %s' % word, 1))
                feature_sets[t].append(('pos t: %s' % pos, 1))

                # word identity and POS tag context

                for delta in range(1, self.delta+1):

                    if delta == 0:
                        continue

                    if t - delta >= 0: # left
                        word, pos = observation[t-delta].split()
                        feature_sets[t].append(('word identity t-%d: %s' % (delta, word), 1))
                        feature_sets[t].append(('pos t-%d: %s' % (delta, pos), 1))

                    if t + delta < len_observation: # right
                        word, pos = observation[t+delta].split()
                        feature_sets[t].append(('word identity t+%d: %s' % (delta, word), 1))
                        feature_sets[t].append(('pos t+%d: %s' % (delta, pos), 1))

                if t >= 1:

                    word_i, pos_i = observation[t-1].split()
                    word_j, pos_j = observation[t].split()
                        
                    feature_sets[t].append(('word pair (t-1, t): (%s %s)' % (word_i, word_j), 1))
                    feature_sets[t].append(('POS pair (t-1, t): (%s %s)' % (pos_i, pos_j), 1))

                if t >= 2:

                    word_i, pos_i = observation[t-2].split()
                    word_j, pos_j = observation[t-1].split()
                        
                    feature_sets[t].append(('POS pair (t-2, t-1): (%s %s)' % (pos_i, pos_j), 1))

                if t >= 1 and t < len_observation-1:

                    word_i, pos_i = observation[t-1].split()
                    word_j, pos_j = observation[t+1].split()
                        
                    feature_sets[t].append(('word pair (t-1, t+1): (%s %s)' % (word_i, word_j), 1))
                    feature_sets[t].append(('POS pair (t-1, t+1): (%s %s)' % (pos_i, pos_j), 1))

                if t < len_observation-1:

                    word_i, pos_i = observation[t].split()
                    word_j, pos_j = observation[t+1].split()

                    feature_sets[t].append(('word pair (t, t+1): (%s %s)' % (word_i, word_j), 1))
                    feature_sets[t].append(('POS pair (t, t+1): (%s %s)' % (pos_i, pos_j), 1))

                if t < len_observation-2:

                    word_i, pos_i = observation[t+1].split()
                    word_j, pos_j = observation[t+2].split()

                    feature_sets[t].append(('POS pair (t+1, t+2): (%s %s)' % (pos_i, pos_j), 1))

            elif self.corpus_id in ['wsj', 'multexteast']:

                # word identity 

                feature_sets[t].append(('word identity t: %s' % observation[t], 1))

                # prefix

                for stop in range(1, len(observation[t])-1):
                
                    prefix = observation[t][:stop]
                    if len(prefix) <= 6:
                        feature_sets[t].append(('prefix t: %s' % prefix, 1))
                        
                # suffix

                for start in range(1, len(observation[t])):

                    suffix = observation[t][start:]
                    if len(suffix) <= 6:
                        feature_sets[t].append(('suffix t: %s' % suffix, 1))

                # regular expressions

                for (pattern, reg_exp) in self.reg_exps:
                    if reg_exp.search(observation[t]) != None: # check if active
                        pass
                        if t == 1:
                            feature_sets[t].append(('regexp (t) = %s, t = 1' % pattern, 1))
                        else:
                            feature_sets[t].append(('regexp (t) = %s, t != 1' % pattern, 1))

                # word identity context 

                for delta in range(1, self.delta+1):

                    if delta == 0:
                        continue

                    if t - delta >= 0: # left
                        feature_sets[t].append(('word identity t-%d: %s' % (delta, observation[t-delta]), 1))

                    if t + delta < len_observation: # right
                        feature_sets[t].append(('word identity t+%d: %s' % (delta, observation[t+delta]), 1))

                if t >= 1:

                    feature_sets[t].append(('word pair (t-1, t): (%s %s)' % (observation[t-1], observation[t]), 1))

                if t < len_observation-1:

                    feature_sets[t].append(('word pair (t, t+1): (%s %s)' % (observation[t], observation[t+1]), 1))

                if t >= 1 and t < len_observation-1:
                    
                    feature_sets[t].append(('word pair (t-1, t+1): (%s %s)' % (observation[t-1], observation[t+1]), 1))                    

            elif self.corpus_id in ['genia', 'geniatb']:

                # word identity 

                feature_sets[t].append(('word identity t: %s' % observation[t], 1))

                # generalized word class (Collins, 2002)

                generalization = self.make_long_generalized_word_class(observation[t])
                feature_sets[t].append(('long generalized word class t: %s' % generalization, 1))
                generalization = self.make_brief_generalized_word_class(observation[t])
                feature_sets[t].append(('brief generalized word class t: %s' % generalization, 1))                

                # prefix

                for stop in range(1, len(observation[t])-1):
                
                    prefix = observation[t][:stop]
                    if len(prefix) <= 6:
                        feature_sets[t].append(('prefix t: %s' % prefix, 1))
                        
                # suffix

                for start in range(1, len(observation[t])):

                    suffix = observation[t][start:]
                    if len(suffix) <= 6:
                        feature_sets[t].append(('suffix t: %s' % suffix, 1))

                # regular expressions

                for (pattern, reg_exp) in self.reg_exps:
                    if reg_exp.search(observation[t]) != None: # check if active
                        if t == 1:
                            feature_sets[t].append(('regexp (t) = %s, t = 1' % pattern, 1))
                        else:
                            feature_sets[t].append(('regexp (t) = %s, t != 1' % pattern, 1))

                # word identity context 

                for delta in range(1, self.delta+1):

                    if delta == 0:
                        continue

                    if t - delta >= 0: # left
                        feature_sets[t].append(('word identity t-%d: %s' % (delta, observation[t-delta]), 1))

                    if t + delta < len_observation: # right
                        feature_sets[t].append(('word identity t+%d: %s' % (delta, observation[t+delta]), 1))

                if t >= 1:

                    feature_sets[t].append(('word pair (t-1, t): (%s %s)' % (observation[t-1], observation[t]), 1))

                if t < len_observation-1:

                    feature_sets[t].append(('word pair (t, t+1): (%s %s)' % (observation[t], observation[t+1]), 1))

                if t >= 1 and t < len_observation-1:
                    
                    feature_sets[t].append(('word pair (t-1, t+1): (%s %s)' % (observation[t-1], observation[t+1]), 1))                    

        feature_sets.append([('BIAS', 1), ('word identity t </s>', 1)])

        return feature_sets

    
    def make_long_generalized_word_class(self, word):
        # (Collins, 2002; Settles, 2004)

        word = re.sub('[A-Z]', 'A', word)
        word = re.sub('[a-z]', 'a', word)
        word = re.sub('[0-9]', '0', word)
        word = re.sub('[^Aa0]', '_', word)

        return word


    def make_brief_generalized_word_class(self, word):
        # (Collins, 2002; Settles, 2004)

        word = re.sub('[A-Z]', 'A', word)
        word = re.sub('[a-z]', 'a', word)
        word = re.sub('[0-9]', '0', word)
        word = re.sub('[^Aa0]', '_', word)

        word = re.sub('A+', 'A', word)
        word = re.sub('a+', 'a', word)
        word = re.sub('0+', '0', word)
        word = re.sub('_+', '_', word)

        return word

    

