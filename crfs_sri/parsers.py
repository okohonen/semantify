

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

    def __init__(self, data_file):

        super(TrainFileParser, self).__init__(data_file)

        return

    
    def parse(self, instance_index):

        self.FILE.seek(self.instance_positions[instance_index])
            
        observation = []
        output = {}

        output[(0, 0)] = 'START' 
        observation = ['<s>']
                
        while(1):
                    
            line = self.FILE.readline().strip()
            
            if line:

                line = line.split('\t')
                output[(0, len(observation))] = line[-1]
                observation.append(line[:-1])

            else:
                
                break
                            
        output[(0, len(observation))] = 'STOP'
        observation.append('</s>')

        return observation, len(observation), output


class DevelFileParser(Parser):

    def __init__(self, data_file):

        super(DevelFileParser, self).__init__(data_file)

        return

    
    def parse(self, instance_index):

        self.FILE.seek(self.instance_positions[instance_index])

        observation = ['<s>']
                
        while(1):
                    
            line = self.FILE.readline().strip()
            
            if line:

                line = line.split('\t')
                observation.append(line[:-1])

            else:
                
                break
                            
        observation.append('</s>')

        return observation, len(observation)



class TestFileParser(Parser):

    def __init__(self, data_file):

        super(TestFileParser, self).__init__(data_file)

        return

    
    def parse(self, instance_index):

        self.FILE.seek(self.instance_positions[instance_index])

        observation = ['<s>']
                
        while(1):
                    
            line = self.FILE.readline().strip()
            
            if line:

                line = line.split('\t')
                observation.append(line)

            else:
                
                break
                            
        observation.append('</s>')

        return observation, len(observation)




class PredictionFileParser(Parser):

    def __init__(self, data_file):

        super(PredictionFileParser, self).__init__(data_file)

        return


    def parse(self, instance_index):

        self.FILE.seek(self.instance_positions[instance_index])

        observation = []
        output = {}

        output[(0, 0)] = 'START' 
        observation = ['<s>']

        while(1):

            line = self.FILE.readline().strip()
            
            if line:

                line = line.split('\t')
                output[(0, len(observation))] = line[-1]
                observation.append(line[:-1])

            else:
                
                break
                
        output[(0, len(observation))] = 'STOP'
        observation.append('</s>')
            
        return observation, len(observation), output




class ReferenceFileParser(Parser):

    def __init__(self, data_file):

        super(ReferenceFileParser, self).__init__(data_file)

        return


    def parse(self, instance_index):

        self.FILE.seek(self.instance_positions[instance_index])

        observation = []
        output = {}

        output[(0, 0)] = 'START' 
        observation = ['<s>']

        while(1):

            line = self.FILE.readline().strip()
            
            if line:

                line = line.split('\t')
                output[(0, len(observation))] = line[-1]
                observation.append(line[:-1])

            else:
                
                break
                
        output[(0, len(observation))] = 'STOP'
        observation.append('</s>')

        return observation, len(observation), output
