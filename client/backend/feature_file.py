import gzip
# Wrapper for the feature file format

class StringFeatureFileWriter:
    def __init__(self, fp):
        self.fp = fp
        
    def append_sentence(self, lines):
        print lines
        self.fp.write("".join(lines).encode("utf-8"))
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

def extractlabel(line):
    parts = line.split("\t")
    return parts[-1].strip()

def labels(inputf):        
    if inputf[-3:] == ".gz":
        fp = gzip.open(inputf)
    else:
        fp = open(inputf)
    for line in fp:
        if line == "\n":
            continue
        yield extractlabel(line)
    fp.close()
