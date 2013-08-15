
class Parser(object):

    def __init__(self, data_file):

        self.data_file = data_file

        self.instance_positions, self.size = self.process()

        return


    def open(self):

        self.FILE = open(self.data_file, 'r')

        return


    def close(self): 

        self.FILE.close()
        self.FILE = None

        return


    def process(self):

        self.open()

        instance_positions = []

        while(1):

            position = self.FILE.tell() 
            line = self.FILE.readline().strip() 

            if not line:
                
                break
            
            else:

                instance_positions.append(position)

        self.close()

        return instance_positions, len(instance_positions)



class TrainFileParser(Parser):

    def __init__(self, data_file, tagset_id = None):

        super(TrainFileParser, self).__init__(data_file)

        self.tagset_id = tagset_id

        return


    def parse(self, instance_index):

        self.FILE.seek(self.instance_positions[instance_index])
        line = self.FILE.readline().strip()

        observation = ['<s>']
        output = {}

        line = line.split(',')[0] # throw away multiple analyses
        line = line.split('\t')[1] # throw away word, keep analysis
        line = line.split(' ') # split analysis 

        t_word = 1
        for analysis_segment in line:
            segment = analysis_segment.split(':')[0]
            t_seg = 1
            for char in segment:
                observation.append(char)
                if t_seg == 1:
                    output[t_word] = 'B'
                else:
                    output[t_word] = 'M'
                t_seg += 1
                t_word += 1

        output[0] = 'START' 
        output[t_word] = 'STOP' 
        observation.append('</s>')

        # choose number of tags 

        if self.tagset_id == 'BM':

            pass

        if self.tagset_id == 'BMS':
            
            for t in range(len(observation)-1):

                if output[t] == 'B':
                    if output[t+1] == 'B':
                        output[t] = 'S'
                    if output[t+1] == 'M':
                        output[t] = 'B'
                    if output[t+1] == 'STOP':
                        output[t] = 'S'
                elif output[t] == 'M':
                    pass

        elif self.tagset_id == 'BMES':
            
            for t in range(len(observation)-1):

                if output[t] == 'B':
                    if output[t+1] == 'B':
                        output[t] = 'S'
                    if output[t+1] == 'I':
                        output[t] = 'B'
                    if output[t+1] == 'STOP':
                        output[t] = 'S'
                elif output[t] == 'I':
                    if output[t+1] == 'B':
                        output[t] = 'E'
                    if output[t+1] == 'I':
                        output[t] = 'M'
                    if output[t+1] == 'STOP':
                        output[t] = 'E'
                    
        # make doubleton cliques
        for t in range(len(observation)-1):
            output[(t, t+1)] = (output[t], output[t+1])

        return observation, len(observation), output





class DevelFileParser(Parser):

    def __init__(self, data_file, token_eval):

        super(DevelFileParser, self).__init__(data_file)

        self.token_eval = token_eval

        return


    def parse(self, instance_index):

        self.FILE.seek(self.instance_positions[instance_index])
        line = self.FILE.readline().strip()

        if self.token_eval == False:

            observation = ['<s>']

            line = line.split('\t')[0] # throw away analysis, keep word

            t_word = 1
            for char in line:
                observation.append(char)
                t_word += 1

            observation.append('</s>')
 
        else:

            observation = ['<s>']

            line = line.split(' ')[1:] # throw away word frequency
            line = ''.join(line)

            t = 1
            for char in line:
                observation.append(char)
                t += 1

            observation.append('</s>')

        return observation, len(observation)






class TestFileParser(Parser):

    def __init__(self, data_file):

        super(TestFileParser, self).__init__(data_file)

        return


    def parse(self, instance_index):

        self.FILE.seek(self.instance_positions[instance_index])
        line = self.FILE.readline().strip()

        observation = ['<s>']  
        
        t = 1
        for char in line:
            observation.append(char)
            t += 1

        observation.append('</s>')
            

        return observation, len(observation)




