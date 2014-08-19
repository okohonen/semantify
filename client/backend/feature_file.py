import gzip
import devutil
# Wrapper for the feature file format

class StringFeatureFileWriter:
    def __init__(self, fp):
        self.fp = fp
        
    def append_sentence(self, lines):
        self.fp.write("".join(lines).encode("utf-8"))
        self.fp.write("\n")

    def close(self):
        self.fp.close()

    def __del__(self):
        self.close()

class StringFeatureFileReader:
    def __init__(self, fp, encoding = None):
        self.fp = fp
        self.encoding = encoding

    def sentences(self):
        lines = []
        for line in self.fp:
            if line=="\n":
                yield lines
                lines = []
            elif self.encoding is None:
                lines.append(line)
            else:
                lines.append(line.decode(self.encoding))

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
