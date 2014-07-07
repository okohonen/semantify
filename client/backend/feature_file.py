# Wrapper for the feature file format

class StringFeatureFileWriter:
    def __init__(self, fp):
        self.fp = fp
        
    def append_sentence(self, lines):
        self.fp.write("".join(lines))
        self.fp.write("\n")

class StringFeatureFileReader:
    def __init__(self, fp):
        self.fp = fp

    def sentences(self):
        lines = []
        for line in self.fp:
            if line=="\n":
                yield lines
                lines = []
            else:
                lines.append(line)
