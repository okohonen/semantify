#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import sys
import copy
import time
import gzip
import numpy
from numpy import array, zeros, ones, mean, average, tile, nonzero, \
    newaxis, isnan, isfinite



class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class FileFormatError(Error):
    """Base class for exceptions in this module."""
    pass

class LengthMismatchError(Error):

    def __init__(self, len1, len2):
        self.len1 = len1
        self.len2 = len2

    def __str__(self):
        return "mismatched lengths: %s, %s" % (self.len1, self.len2)

class Segmentation:
    """Stores the segmentations of words"""

    def __init__(self):
        self.data = {}
        self.wlist = []

    def get_words(self):
        """Return the list of words"""
        return self.wlist

    def get_size(self):
        """Return the number of words"""
        return len(self.wlist)

    def get_segmentation(self, w):
        """Return the segmentation for given word"""
        return self.data[w]

    def string2bvect(self, mstr):
        """Convert segmentation to boundary vector"""
        v = []
        i = 1
        while i < len(mstr):
            l = mstr[i]
            if l == ' ':
                v.append(1)
                i += 1
            else:
                v.append(0)
            i += 1
        return numpy.array(v)

    def load(self, filename, wset=None):
        """Load segmentations from given file.

        Given the list or dict wset, load only the words found in it.

        """
        if filename[-3:] == '.gz':
            fobj = gzip.open(filename, 'r')
        else:
            fobj = open(filename, 'r')
        for line in fobj:
            if line[0] == '#':
                continue
            line = line.rstrip()
            if '\t' in line:
                w, a = line.split('\t')
            else:
                a = line
                w = a.split(', ')[0].translate(None, ' ')
            if wset == None or w in wset:
                self.wlist.append(w)
                self.data[w] = []
                for mstr in a.split(', '):
                    b = self.string2bvect(mstr)
                    self.data[w].append(b)
        fobj.close()

    def equalize(self, ref):
        """Remove words that are not in the given segmentation instance"""
        for w in self.wlist:
            if not w in ref.data:
                del self.data[w]
        self.wlist = copy.copy(ref.wlist)

class TokenSegmentation(Segmentation):

    def __init__(self):
        self.data = []

    def get_words(self):
        """Return the list of words"""
        return [x[0] for x in self.data]

    def get_size(self):
        """Return the number of words"""
        return len(self.data)

    def get_segmentation(self, w):
        """Return the segmentation for given word"""
        return [x[2] for x in self.data if x[0] == w]

    def load(self, filename):
        """Load segmentations from given file."""
        if filename[-3:] == '.gz':
            fobj = gzip.open(filename, 'r')
        else:
            fobj = open(filename, 'r')
        for line in fobj:
            if line[0] == '#':
                continue
            line = line.rstrip()
            c, a = line.split(' ', 1)
            w = a.translate(None, ' ')
            b = self.string2bvect(a)
            self.data.append((w, float(c), b))
        fobj.close()
    
    def equalize(self, ref):
        """Remove words that are not in the given segmentation instance"""
        for t in self.data:
            w = t[0]
            if not w in ref.data:
                del self.data[t]

def _recall_eval_single(pre, ref):
    """Calculate recall for boundary vectors"""
    if pre.shape[0] != ref.shape[0]:
        raise LengthMismatchError(pre.shape[0], ref.shape[0])
    tot = ref.sum()
    if tot == 0:
        return 1.0, 0
    diff = ref - pre
    E = (abs(diff) + diff) / 2 # recall errors
    r = float(tot - E.sum()) / tot
    return r, tot

def _recall_eval(predicted, reference, weights=None, micro=False):
    """Calculate recall for the segmentations of words"""
    wlist = reference.get_words()
    total = 0
    s = 0.0
    for i in range(len(wlist)):
        w = wlist[i]
        if len(w) < 2:
            # Skip one letter words
            continue
        refA = reference.get_segmentation(w)
        preA = predicted.get_segmentation(w)
        maxr = 0
        maxtot = -1
        for ref in refA:
            tot = ref.sum()
            if tot == 0:
                maxr = 1.0
                maxtot = 0
                continue
            for pre in preA:
                try:
                    r, tmp = _recall_eval_single(pre, ref)
                except LengthMismatchError:
                    sys.stderr.write("Error while processing '%s'\n" % w)
                    raise
                if maxtot == -1 or r > maxr:
                    maxr = r
                    maxtot = tot
        if micro:
            # Micro-average: 
            # maxr is number of correct boundaries, maxtot is total
            maxr = maxtot * maxr
        else:
            # Macro-average: 
            # maxr is proportion of correct boundaries, maxtot is one
            maxtot = 1
        if weights == None:
            total += maxtot
            s += maxr
        else:
            total += weights[i] * maxtot
            s += weights[i] * maxr
    if total > 0:
        return s / total, total
    else:
        return 1.0, 0

def _strict_eval(predicted, reference, weights=None, micro=False):
    """Calculate recall for the segmentations of words using strict
    macthing of alternatives"""
    import munkres
    wlist = reference.get_words()
    rec_total = 0
    pre_total = 0
    rec_sum = 0.0
    pre_sum = 0.0
    for k in range(len(wlist)):
        w = wlist[k]
        if len(w) < 2:
            continue
        refA = reference.get_segmentation(w)
        preA = predicted.get_segmentation(w)
        
        ref_altnum = len(refA)
        pre_altnum = len(preA)
        n = max(ref_altnum, pre_altnum)
        w = [[0 for v in range(n)] for u in range(n)]
        results = {}
        
        for i in range(n):
            for j in range(n):
                if i < ref_altnum and j < pre_altnum:
                    rec_r, rec_t = _recall_eval_single(preA[j], refA[i])
                    pre_r, pre_t = _recall_eval_single(refA[i], preA[j])
                else:
                    pre_r = 0.0
                    rec_r = 0.0
                results[(i,j)] = (pre_r, rec_r)
                if pre_r + rec_r == 0:
                    f = 0.0
                else:
                    f = 2.0*pre_r*rec_r/(pre_r+rec_r)
                w[i][j] = 1.0 - f # cost

        m = munkres.Munkres()
        indexes = m.compute(w)

        if micro:
            pre_w, ref_w = 1, 1
            if weights != None:
                # Weights are evenly distributed to the alternative analyses
                pre_w = weights[k] / float(pre_altnum)
                ref_w = weights[k] / float(ref_altnum)
            # Sum over all matched analyses
            for i, j in indexes:
                if j < pre_altnum:
                    pre_n = preA[j].sum()
                    pre_sum += pre_w * results[(i,j)][0] * pre_n
                    pre_total += pre_w * pre_n
                if i < ref_altnum:
                    ref_n = refA[i].sum()
                    rec_sum += ref_w * results[(i,j)][1] * ref_n
                    rec_total += ref_w * ref_n
        else:
            # Average over matched analyses
            pre_t = 0.0
            rec_t = 0.0
            for i, j in indexes:
                pre_t += results[(i,j)][0]
                rec_t += results[(i,j)][1]
            pre_t = pre_t / len(preA)
            rec_t = rec_t / len(refA)
            
            if weights == None:
                pre_sum += pre_t
                pre_total += 1
                rec_sum += rec_t
                rec_total += 1
            else:
                pre_sum += weights[k] * pre_t
                pre_total += weights[k]
                rec_sum += weights[k] * rec_t
                rec_total += weights[k]

    if pre_total == 0:
        pre_r = 1.0
    else:
        pre_r = pre_sum / pre_total
    if rec_total == 0:
        rec_r = 1.0
    else:
        rec_r = rec_sum / rec_total
    return pre_r, rec_r, pre_total, rec_total

def _token_eval(predicted, reference):
    """Calculate recall for the segmentations of words"""
    rec_total = 0
    pre_total = 0
    rec_sum = 0.0
    pre_sum = 0.0
    for w, count, ref in reference.data:
        preA = predicted.get_segmentation(w)
        pre_alts = len(preA)
        bestj = -1
        bestf = -1
        for j in range(pre_alts):
            rec_r, rec_t = _recall_eval_single(preA[j], ref)
            pre_r, pre_t = _recall_eval_single(ref, preA[j])
            if pre_r + rec_r == 0:
                f = 0.0
            else:
                f = 2.0*pre_r*rec_r/(pre_r+rec_r)
            if f > bestf:
                bestf = f
                bestj = j

        rec_r, rec_t = _recall_eval_single(preA[bestj], ref)
        pre_r, pre_t = _recall_eval_single(ref, preA[bestj])
        pre_sum += count * pre_r * pre_t
        pre_total += count * pre_t
        rec_sum += count * rec_r * rec_t
        rec_total += count * rec_t
    if pre_total == 0:
        pre_r = 1.0
    else:
        pre_r = pre_sum / pre_total
    if rec_total == 0:
        rec_r = 1.0
    else:
        rec_r = rec_sum / rec_total
    return pre_r, rec_r, pre_total, rec_total

def _load_weights(filename, reverse=False):
    """Load word weights from a file"""
    if filename.endswith('.gz'):
        fobj = gzip.open(filename, 'r')
    else:
        fobj = open(filename, 'r')
    wdict = {}
    for line in fobj:
        line = line.rstrip() 
        if reverse:
            weight, word = line.split(None, 1)
        else:
            word, weight = line.split(None, 1)
        wdict[word] = float(weight)
    fobj.close()
    return wdict

def run_evaluation(options):

    if options.tokens:
        goldstd = TokenSegmentation()
        try:
            goldstd.load(options.goldFile)
        except ValueError as e:
            sys.stderr.write("Error: %s\n" % e)
            raise FileFormatError("Could not load reference data")
    else:
        if options.weightFile != None:
            try:
                wdict = _load_weights(options.weightFile)
            except Exception as e1:
                try:
                    wdict = _load_weights(options.weightFile, reverse=True)
                except Exception as e2:
                    sys.stderr.write("Error case 1: %s\n" % e1)
                    sys.stderr.write("Error case 2: %s\n" % e2)
                    raise FileFormatError("Could not load word weights")
        else:
            wdict = None

        goldstd = Segmentation()
        try:
            goldstd.load(options.goldFile, wdict)
        except ValueError as e:
            sys.stderr.write("Error: %s\n" % e)
            raise FileFormatError("Could not load reference data")

        if wdict != None:
            wlist = goldstd.get_words()
            weights = zeros(len(wlist))
            for i in range(len(wlist)):
                word = wlist[i]
                weights[i] = wdict[word]
        else:
            weights = None

    predicted = Segmentation()
    try:
        predicted.load(options.predFile, goldstd.get_words())
    except ValueError as e:
        sys.stderr.write("Error: %s\n" % e)
        raise FileFormatError("Could not load predicted data")
    goldstd.equalize(predicted)

    if options.tokens:
        pre, rec, pren, recn = _token_eval(predicted, goldstd)
    elif options.strictalts:
        pre, rec, pren, recn = _strict_eval(predicted, goldstd, 
                                            weights=weights, 
                                            micro=options.micro)
    else:
        rec, recn = _recall_eval(predicted, goldstd, weights=weights, 
                                 micro=options.micro)
        pre, pren = _recall_eval(goldstd, predicted, weights=weights, 
                                 micro=options.micro)

    if pre > 0 and rec > 0:
        f = 2.0/(1.0/pre+1.0/rec)
    else:
        f = 0.0
    return pre, rec, f, pren, recn

def main(argv):
    from optparse import OptionParser
    usage = """Usage: %prog -g goldFile -p predFile [options]"""

    parser = OptionParser(usage=usage)
    parser.add_option("-g", "--goldFile", dest="goldFile",
                      default = None,
                      help="gold standard segmentation file")
    parser.add_option("-p", "--predFile", dest="predFile",
                      default = None,
                      help="predicted segmentation file")
    parser.add_option("-s", "--strictalts", dest="strictalts",
                      default = False, action = "store_true",
                      help="strict matching of alternative analyses")
    parser.add_option("-m", "--micro", dest="micro",
                      default = False, action = "store_true",
                      help="use micro-average instead of macro-average")
    parser.add_option("-w", "--weightFile", dest="weightFile",
                      default = None,
                      help="read word weights from file")
    parser.add_option("-t", "--tokens", dest="tokens",
                      default = False, action = "store_true",
                      help="use token-based micro-average")
    (options, args) = parser.parse_args(argv[1:])

    if options.goldFile == None or options.predFile == None:
        parser.print_help()
        sys.exit()

    ts = time.time()
    pre, rec, f, pren, recn = run_evaluation(options)
    te = time.time()

    print "# Gold standard file: %s" % options.goldFile
    print "# Predictions file  : %s" % options.predFile
    print "# Evaluation options:"
    if options.tokens:
        print "# - using token-based micro-average (--tokens)"
        print "# Recall based on %s boundaries" % recn
        print "# Precision based on %s boundaries" % pren
    else:
        if options.weightFile != None:
            print "# - word weights loaded from %s" % options.weightFile
        if options.micro:
            print "# - using micro-averages (--micro)"
        else:
            print "# - using macro-averages"
        if options.strictalts:
            print "# - strict matching of alternative analyses (--strictalts)"
        else:
            print "# - best local matching of alternative analyses"
        if options.micro:
            print "# Recall based on %s boundaries" % recn
            print "# Precision based on %s boundaries" % pren
        else:
            print "# Recall based on %s words" % recn
            print "# Precision based on %s words" % pren
    print "# Evaluation time: %.2fs" % (te-ts)
    print
    print "precision: %s" % pre
    print "recall   : %s" % rec
    print "fmeasure : %s" % f

if __name__ == "__main__":
    main(sys.argv)
