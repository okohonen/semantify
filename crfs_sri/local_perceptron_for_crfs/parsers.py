

class Parser(object):

    def __init__(self, data_file, corpus_id, task_id):

        self.data_file = data_file
        self.corpus_id = corpus_id
        self.task_id = task_id

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

        previous_line_was_empty = True
        
        while(1):

            position = self.FILE.tell()
            line = self.FILE.readline().strip() 

            if not line and previous_line_was_empty:
                
                break
            
            elif not line and not previous_line_was_empty:

                previous_line_was_empty = True

            elif line and previous_line_was_empty:

                instance_positions.append(position)
                
                previous_line_was_empty = False

            elif line and not previous_line_was_empty:

                previous_line_was_empty = False

        instance_positions = instance_positions

        self.close()

        return instance_positions, len(instance_positions)




class TrainFileParser(Parser):

    def __init__(self, data_file, corpus_id, task_id):

        super(TrainFileParser, self).__init__(data_file, corpus_id, task_id)

        return

    
    def parse(self, instance_index):

        if self.corpus_id in ['conll2000', 'conll1999']:

            if self.task_id == 'chunking-bio':

                self.FILE.seek(self.instance_positions[instance_index])
            
                observation = []
                output = {}

                output[(0, 0)] = 'START' 
                observation = ['<s> START']
                
                while(1):
                    
                    line = self.FILE.readline().strip()
            
                    if line:

                        line = line.split()
                        output[(0, len(observation))] = line[2]
                        observation.append(line[0] + " " + line[1])

                    else:
                
                        break
                            
                output[(0, len(observation))] = 'STOP'
                observation.append('</s> STOP')

            elif self.task_id == 'chunking-io':

                self.FILE.seek(self.instance_positions[instance_index])
            
                observation = []
                output = {}

                output[(0, 0)] = 'START' 
                observation = ['<s> START']
                
                while(1):
                    
                    line = self.FILE.readline().strip()
            
                    if line:

                        line = line.split()
                        if line[2] == 'O':
                            output[(0, len(observation))] = line[2]
                        else:
                            output[(0, len(observation))] = line[2][2:]

                        observation.append(line[0] + " " + line[1])

                    else:
                
                        break
                            
                output[(0, len(observation))] = 'STOP'
                observation.append('</s> STOP')

        elif self.corpus_id == 'genia':

            if self.task_id == 'chunking-bio':

                self.FILE.seek(self.instance_positions[instance_index])
            
                observation = []
                output = {}

                output[(0, 0)] = 'START' 
                observation = ['<s> START']
                
                while(1):
                    
                    line = self.FILE.readline().strip()
            
                    if line:

                        line = line.split()
                        output[(0, len(observation))] = line[1]
                        observation.append(line[0])

                    else:
                
                        break
                            
                output[(0, len(observation))] = 'STOP'
                observation.append('</s> STOP')

            elif self.task_id == 'chunking-io':

                self.FILE.seek(self.instance_positions[instance_index])
            
                observation = []
                output = {}

                output[(0, 0)] = 'START' 
                observation = ['<s> START']
                
                while(1):
                    
                    line = self.FILE.readline().strip()
            
                    if line:

                        line = line.split()
                        if line[1] == 'O':
                            output[(0, len(observation))] = line[1]
                        else:
                            output[(0, len(observation))] = line[1][2:]

                        observation.append(line[0])

                    else:
                
                        break
                            
                output[(0, len(observation))] = 'STOP'
                observation.append('</s> STOP')

        elif self.corpus_id in ['wsj', 'geniatb']:

            self.FILE.seek(self.instance_positions[instance_index])

            observation = []
            output = {}

            if self.task_id in ['tagging-and-chunking-bio', 'tagging-and-chunking-io', 'X-tagging-and-chunking-bio', 'X-tagging-and-chunking-io']:

                output[(0, 0)] = 'START' 
                output[(1, 0)] = 'START' 
                observation = ['<s>']

            elif self.task_id in ['joint-tagging-and-chunking-bio', 'joint-tagging-and-chunking-io']:

                output[(0, 0)] = 'START START' 
                output[(1, 0)] = 'START START' 
                observation = ['<s>']

            else:

                output[(0, 0)] = 'START' 
                observation = ['<s>']
                
            while(1):
                    
                line = self.FILE.readline().strip()
            
                if line:

                    line = line.split()

                    if self.task_id in ['tagging-and-chunking-bio', 'X-tagging-and-chunking-bio']:

                        output[(0, len(observation))] = line[1]
                        output[(1, len(observation))] = line[2]                            

                    elif self.task_id in ['tagging-and-chunking-io', 'X-tagging-and-chunking-io']:

                        output[(0, len(observation))] = line[1]

                        if line[2] == 'O':
                            output[(1, len(observation))] = line[2]
                        else:
                            output[(1, len(observation))] = line[2][2:]

                    elif self.task_id == 'joint-tagging-and-chunking-bio':

                        output[(0, len(observation))] = line[1] + " " + line[2]

                    elif self.task_id == 'joint-tagging-and-chunking-io':

                        if line[2] == 'O':
                            output[(0, len(observation))] = line[1] + " " + line[2]
                        else:
                            output[(0, len(observation))] = line[1] + " " + line[2][2:]

                    elif self.task_id == 'tagging':

                        output[(0, len(observation))] = line[1]

                    elif self.task_id == 'chunking-bio':

                        output[(0, len(observation))] = line[2]

                    elif self.task_id == 'chunking-io':

                        if line[2] == 'O':
                            output[(0, len(observation))] = line[2]
                        else:
                            output[(0, len(observation))] = line[2][2:]

                    observation.append(line[0])
                
                else:
                
                    break
                
            if self.task_id in ['tagging-and-chunking-bio', 'tagging-and-chunking-io', 'X-tagging-and-chunking-bio', 'X-tagging-and-chunking-io']:

                output[(0, len(observation))] = 'STOP'
                output[(1, len(observation))] = 'STOP'
                observation.append('</s>')

            elif self.task_id in ['joint-tagging-and-chunking-bio', 'joint-tagging-and-chunking-io']:

                output[(0, len(observation))] = 'STOP STOP'
                output[(1, len(observation))] = 'STOP STOP'
                observation.append('</s>')
                
            else:

                output[(0, len(observation))] = 'STOP'
                observation.append('</s>')

        elif self.corpus_id in ['multexteast']:
        
            self.FILE.seek(self.instance_positions[instance_index])

            observation = []
            output = {}

            output[(0, 0)] = 'START' 
            observation = ['<s>']

            while(1):

                line = self.FILE.readline().strip()
            
                if line:

                    line = line.split()
                    output[(0, len(observation))] = line[1]
                    observation.append(line[0])

                else:
                
                    break
                
            output[(0, len(observation))] = 'STOP'
            observation.append('</s>')

        return observation, len(observation), output






class DevelFileParser(Parser):

    def __init__(self, data_file, corpus_id, task_id):

        super(DevelFileParser, self).__init__(data_file, corpus_id, task_id)

        return

    
    def parse(self, instance_index):

        if self.corpus_id in ['conll2000', 'conll1999']:

            self.FILE.seek(self.instance_positions[instance_index])

            observation = ['<s> START']
                
            while(1):
                    
                line = self.FILE.readline().strip()
            
                if line:

                    line = line.split()
                    observation.append(line[0] + " " + line[1])

                else:
                
                    break
                            
            observation.append('</s> STOP')

        else:
            
            self.FILE.seek(self.instance_positions[instance_index])

            observation = ['<s>']

            while(1):

                line = self.FILE.readline().strip()
            
                if line:

                    line = line.split()
                    observation.append(line[0])

                else:
                
                    break
                
            observation.append('</s>')

        return observation, len(observation)



class TestFileParser(Parser):

    def __init__(self, data_file, corpus_id, task_id):

        super(TestFileParser, self).__init__(data_file, corpus_id, task_id)

        return

    
    def parse(self, instance_index):

        if self.corpus_id in ['conll2000', 'conll1999']:

            self.FILE.seek(self.instance_positions[instance_index])

            observation = ['<s> START']
                
            while(1):
                    
                line = self.FILE.readline().strip()
            
                if line:

                    line = line.split()
                    observation.append(line[0] + " " + line[1])

                else:
                
                    break
                            
            observation.append('</s> STOP')

        else:
        
            self.FILE.seek(self.instance_positions[instance_index])

            observation = ['<s>']

            while(1):

                line = self.FILE.readline().strip()
            
                if line:

                    observation.append(line)

                else:
                
                    break
                
            observation.append('</s>')

        return observation, len(observation)




class PredictionFileParser(Parser):

    def __init__(self, data_file, corpus_id, task_id):

        super(PredictionFileParser, self).__init__(data_file, corpus_id, task_id)

        return


    def parse(self, instance_index):

        if self.corpus_id in ['conll2000', 'conll1999']:
            
            self.FILE.seek(self.instance_positions[instance_index])
            
            observation = []
            output = {}

            output[(0, 0)] = 'START' 
            observation = ['<s> START']
                
            while(1):
                    
                line = self.FILE.readline().strip()
                
                if line:

                    line = line.split()
                    output[(0, len(observation))] = line[2]
                    observation.append(line[0] + " " + line[1])
                    
                else:
                
                    break
                            
            output[(0, len(observation))] = 'STOP'
            observation.append('</s> STOP')

        elif self.corpus_id == 'genia':

            self.FILE.seek(self.instance_positions[instance_index])
            
            observation = []
            output = {}

            output[(0, 0)] = 'START' 
            observation = ['<s> START']
                
            while(1):
                    
                line = self.FILE.readline().strip()
            
                if line:

                    line = line.split()
                    output[(0, len(observation))] = line[1]
                    observation.append(line[0])

                else:
                
                    break
                            
            output[(0, len(observation))] = 'STOP'
            observation.append('</s> STOP')

        elif self.corpus_id in ['wsj', 'geniatb']:

            self.FILE.seek(self.instance_positions[instance_index])

            observation = []
            output = {}

            if self.task_id in ['tagging-and-chunking-bio', 'tagging-and-chunking-io', 'X-tagging-and-chunking-bio', 'X-tagging-and-chunking-io', 'joint-tagging-and-chunking-bio', 'joint-tagging-and-chunking-io']:

                output[(0, 0)] = 'START' 
                output[(1, 0)] = 'START' 
                observation = ['<s>']

            else:

                output[(0, 0)] = 'START' 
                observation = ['<s>']
                
            while(1):
                    
                line = self.FILE.readline().strip()
            
                if line:

                    line = line.split()

                    if self.task_id in ['tagging-and-chunking-bio', 'tagging-and-chunking-io', 'X-tagging-and-chunking-bio', 'X-tagging-and-chunking-io', 'joint-tagging-and-chunking-bio', 'joint-tagging-and-chunking-io']:

                        output[(0, len(observation))] = line[1]
                        output[(1, len(observation))] = line[2]                            

                    elif self.task_id in ['tagging']:

                        output[(0, len(observation))] = line[1]

                    elif self.task_id in ['chunking-bio', 'chunking-io']:

                        output[(0, len(observation))] = line[2]

                    observation.append(line[0])
                
                else:
                
                    break

            if self.task_id in ['tagging-and-chunking-bio', 'tagging-and-chunking-io', 'X-tagging-and-chunking-bio', 'X-tagging-and-chunking-io', 'joint-tagging-and-chunking-bio', 'joint-tagging-and-chunking-io']:

                output[(0, len(observation))] = 'STOP'
                output[(1, len(observation))] = 'STOP'
                observation.append('</s>')
                
            else:

                output[(0, len(observation))] = 'STOP'
                observation.append('</s>')

        elif self.corpus_id in ['multexteast']:

            self.FILE.seek(self.instance_positions[instance_index])

            observation = []
            output = {}

            output[(0, 0)] = 'START' 
            observation = ['<s>']

            while(1):

                line = self.FILE.readline().strip()
                
                if line:
                    
                    line = line.split()
                    output[(0, len(observation))] = line[1]
                    observation.append(line[0])

                else:
                
                    break
                
            output[(0, len(observation))] = 'STOP'
            observation.append('</s>')

        return observation, len(observation), output





class ReferenceFileParser(Parser):

    def __init__(self, data_file, corpus_id, task_id):

        super(ReferenceFileParser, self).__init__(data_file, corpus_id, task_id)

        return

    def parse(self, instance_index):

        if self.corpus_id in ['conll2000', 'conll1999']:

            if self.task_id == 'chunking-bio':

                self.FILE.seek(self.instance_positions[instance_index])
            
                observation = []
                output = {}

                output[(0, 0)] = 'START' 
                observation = ['<s> START']
                
                while(1):
                    
                    line = self.FILE.readline().strip()
            
                    if line:

                        line = line.split()
                        output[(0, len(observation))] = line[2]
                        observation.append(line[0] + " " + line[1])

                    else:
                
                        break
                            
                output[(0, len(observation))] = 'STOP'
                observation.append('</s> STOP')

            elif self.task_id == 'chunking-io':

                self.FILE.seek(self.instance_positions[instance_index])
            
                observation = []
                output = {}

                output[(0, 0)] = 'START' 
                observation = ['<s> START']
                
                while(1):
                    
                    line = self.FILE.readline().strip()
            
                    if line:

                        line = line.split()
                        if line[2] == 'O':
                            output[(0, len(observation))] = line[2]
                        else:
                            output[(0, len(observation))] = line[2][2:]

                        observation.append(line[0] + " " + line[1])

                    else:
                
                        break
                            
                output[(0, len(observation))] = 'STOP'
                observation.append('</s> STOP')

        elif self.corpus_id == 'genia':

            if self.task_id == 'chunking-bio':

                self.FILE.seek(self.instance_positions[instance_index])
            
                observation = []
                output = {}

                output[(0, 0)] = 'START' 
                observation = ['<s> START']
                
                while(1):
                    
                    line = self.FILE.readline().strip()
            
                    if line:

                        line = line.split()
                        output[(0, len(observation))] = line[1]
                        observation.append(line[0])

                    else:
                
                        break
                            
                output[(0, len(observation))] = 'STOP'
                observation.append('</s> STOP')

            elif self.task_id == 'chunking-io':

                self.FILE.seek(self.instance_positions[instance_index])
            
                observation = []
                output = {}

                output[(0, 0)] = 'START' 
                observation = ['<s> START']
                
                while(1):
                    
                    line = self.FILE.readline().strip()
            
                    if line:

                        line = line.split()
                        if line[1] == 'O':
                            output[(0, len(observation))] = line[1]
                        else:
                            output[(0, len(observation))] = line[1][2:]

                        observation.append(line[0])

                    else:
                
                        break
                            
                output[(0, len(observation))] = 'STOP'
                observation.append('</s> STOP')

        elif self.corpus_id in ['wsj', 'geniatb']:

            self.FILE.seek(self.instance_positions[instance_index])

            observation = []
            output = {}

            if self.task_id in ['tagging-and-chunking-bio', 'tagging-and-chunking-io', 'X-tagging-and-chunking-bio', 'X-tagging-and-chunking-io']:

                output[(0, 0)] = 'START' 
                output[(1, 0)] = 'START' 
                observation = ['<s>']

            else:

                output[(0, 0)] = 'START' 
                observation = ['<s>']
                
            while(1):
                    
                line = self.FILE.readline().strip()
            
                if line:

                    line = line.split()

                    if self.task_id in ['tagging-and-chunking-bio', 'X-tagging-and-chunking-bio', 'joint-tagging-and-chunking-bio']:

                        output[(0, len(observation))] = line[1]
                        output[(1, len(observation))] = line[2]                            

                    elif self.task_id in ['tagging-and-chunking-io', 'X-tagging-and-chunking-io', 'joint-tagging-and-chunking-io']:

                        output[(0, len(observation))] = line[1]

                        if line[2] == 'O':
                            output[(1, len(observation))] = line[2]
                        else:
                            output[(1, len(observation))] = line[2][2:]

                    elif self.task_id == 'tagging':

                        output[(0, len(observation))] = line[1]

                    elif self.task_id == 'chunking-bio':

                        output[(0, len(observation))] = line[2]

                    elif self.task_id == 'chunking-io':

                        if line[2] == 'O':
                            output[(0, len(observation))] = line[2]
                        else:
                            output[(0, len(observation))] = line[2][2:]

                    observation.append(line[0])
                
                else:
                
                    break
                
            if self.task_id in ['tagging-and-chunking-bio', 'tagging-and-chunking-io', 'X-tagging-and-chunking-bio', 'X-tagging-and-chunking-io', 'joint-tagging-and-chunking-bio', 'joint-tagging-and-chunking-io']:            

                output[(0, len(observation))] = 'STOP'
                output[(1, len(observation))] = 'STOP'
                observation.append('</s>')
                
            else:

                output[(0, len(observation))] = 'STOP'
                observation.append('</s>')

        elif self.corpus_id in ['multexteast']:

            self.FILE.seek(self.instance_positions[instance_index])

            observation = []
            output = {}

            output[(0, 0)] = 'START' 
            observation = ['<s>']

            while(1):

                line = self.FILE.readline().strip()
                
                if line:
                    
                    line = line.split()
                    output[(0, len(observation))] = line[1]
                    observation.append(line[0])

                else:
                
                    break
                
            output[(0, len(observation))] = 'STOP'
            observation.append('</s>')

        return observation, len(observation), output
