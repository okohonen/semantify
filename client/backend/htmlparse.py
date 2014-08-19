import feature_file as ff
import re
from bs4 import BeautifulSoup
from bs4 import NavigableString
import bs4
import collections
import gzip
import devutil

def parse_page(page, feature_set, annotated=True, build_node_index=True):
    words, f_ortho1, f_ortho3, f_html, labels, sentences, token_nodes, node_index, tokens=preprocess_file(page, feature_set, build_node_index)
    return ParsedHTML(page, sentences, labels, tokens, node_index, annotated)

# Data structure to store the parsed HTML file. Also allows modifying the HTML with 
# the taggings from a classifier
class ParsedHTML:
    def __init__(self, soup, sentences, labels, tokens, node_index, annotated):
        self.soup = soup
        self.sentences = sentences
        self.labels = labels
        self.tokens = tokens
        self.node_index = node_index
        self.annotated = annotated

    # Allows one to read the parsed html in the same feature extracted format
    # as is stored on disc
    def read_features(self):
        return ff.StringFeatureFileReader(self._read_features_iter())

    def _read_features_iter(self):
        for i in xrange(len(self.sentences)):              
            if self.sentences[i] == "\n":
                yield("\n")
            elif self.annotated:
                yield(self.sentences[i]+"\t"+self.labels[i]+"\n")
            else:
                yield(self.sentences[i] + "\n")

    # Write parsed file to disc
    def write_feature_file(self, filename):
        fp = gzip.open(filename, 'wb')
        for tok in self._read_features_iter():
            fp.write(tok.encode('utf8'))        

    # Read classifier output from file given as argument
    def apply_tagging(self, retfile):
        assert(not(self.node_index is None))
        nodes_to_tag = self._extract_tagged_nodes(retfile)
        print "Nodes to tag: %d" % len(nodes_to_tag)
        print nodes_to_tag
        self._modify_tree(nodes_to_tag)

    def _modified_subtreelist(self, soup, s, taggings, node_pos):
        nodel = []
        lastpos = 0
        for startoffset, endoffset, tag in taggings:            
            startpos = node_pos[0][startoffset]
            endpos = node_pos[1][endoffset]
            nodel.append(soup.new_string(s[lastpos:startpos]))
            span = soup.new_tag('span')
            span['wa-subtypes'] = ""
            span['wa-type'] = tag
            span['class'] = "Semantify_%s" % tag
            span['semantify'] = "auto"
            span.string = s[startpos:endpos]
            nodel.append(span)
            lastpos = endpos
        nodel.append(soup.new_string(s[lastpos:]))
        return nodel
        
    def _modify_tree(self, nodes_to_tag):
        for node, taggings in nodes_to_tag:
            ml = self._modified_subtreelist(self.soup, node.string, taggings, self.node_index[node])
            node.replace_with(ml[0])
            for i in range(1, len(ml)):
                ml[i-1].insert_after(ml[i])
    

    # Takes as input the tagged file and the tokens and then produces a list of taggings
# represented as pairs with offsets in lists of triples :[(node, [(startoffset, endoffset, tags)])]
    def _extract_tagged_nodes(self, retfile):
        ret = []
    
        notags = ['O', 'START', 'STOP']
    
        for node, tags in nodeblocks(retfile, self.tokens, lambda x: x not in notags):
            curtag = tags[0]
            starti = 0
    
            offsets = []
    
            for i in range(len(tags)):
                if tags[i] != curtag:
                    if curtag not in notags:
                        offsets.append((starti, i-1, tags[starti]))
                    starti = i
                    curtag = tags[i]
            if curtag not in notags:
                offsets.append((starti, i, tags[starti]))
            ret.append((node, offsets))
    
        return ret


    # Return the page body as string
    def __str__(self):
        return str(self.soup)

    def get_body(self):
        return self.soup.body
        

# Class that implements tokenization equivalent to nltk.wordpunct_tokenize, but also returns the positions of each match
class WordPunctTokenizer:
    def __init__(self):
        self.wpre = re.compile(r'\w+|[^\w\s]+', re.UNICODE)

    def tokenize(self, s):
        return re.findall(self.wpre, s)
    
    def positioned_tokenize(self, s):
        tokens = []
        tokenstart = []
        tokenend = []
        for m in re.finditer(self.wpre, s):
            tokens.append(m.group(0))
            tokenstart.append(m.start())
            tokenend.append(m.end())
        return tokens, tokenstart, tokenend

def class_features(node):
    # Classname features   
    classname=''; classlong=""; classbrief= ""  
    if node.has_attr('class'): 
        classname=",".join(node['class'])
        if node.name == "span" and "WebAnnotator" in classname:          
            assert False, "WebAnnotator tags should be stripped when this is applied"
        classlong, classbrief=Ortho.generalisation(classname)             
                
    return classname, classlong,  classbrief

def htmlparse(soup):   
    nodestack = [soup.body] # Track nodes to expand
    htmlstack = [[]] # Track position in HTML-tree for feature extraction
    labelstack = ['O'] # Track labeling: All subtrees of a labeled tags have the same label
    blocknrstack = [0] # For finding "sentence" boundaries
    
    nonblocktags=['a', 'abbr', 'b', 'basefont', 'bdo', 'big', 'br', 'dfn', 'em', 'font', 'i', 'img', 'input', 'kbd', 'label', 'q', 's', 'samp', 'select', 'small', 'span', 'strike', 'strong', 'sub', 'sup', 'textarea', 'tt', 'u', 'var']
    maxblocknr = 0

    while(len(nodestack) > 0):
        node = nodestack.pop()
        stack = htmlstack.pop()
        label = labelstack.pop()
        blocknr = blocknrstack.pop()

        if isinstance(node, bs4.Tag):
            # Find the annotation label and add to 'labels' list
            # Interpret automatic tags resubmitted as being correct
            if node.name == "span" and node.has_attr("class") and \
            ("WebAnnotator_" in node['class'][0] or "Semantify_" in node['class'][0]):
                if "WebAnnotator_" in node['class'][0]:
                    label=node['class'][0].replace('WebAnnotator_', '')
                else:
                    label=node['class'][0].replace('Semantify_', '') 
                l = stack
            else:
                l = [node]
                l.extend(stack)                
                # Node starts new block
                if node.name not in nonblocktags:
                    maxblocknr += 1
                    blocknr = maxblocknr
            for c in reversed(node.contents):
                nodestack.append(c)
                htmlstack.append(l)
                labelstack.append(label)
                blocknrstack.append(blocknr)

        elif isinstance(node, bs4.Comment): 
            pass # Ignore comments

        elif isinstance(node, bs4.NavigableString):
            # Ignore script tags
            if node.parent.name != "script":
                yield (node, stack, label, blocknr)
        else:
            print "Unknown tag type"
            devutil.keyboard()
    
    assert(len(htmlstack) == 0)

#     return tokens, labels
 
def traverse_html_nodes(nodeiter, htmlfeaturefuns, tokenfeaturefuns, build_token_index):
    tokens = []
    labels=[]
    node_index = {}
    tok = WordPunctTokenizer()

    for node, stack, label, blocknr in nodeiter:        
        htmlf = {}
        for feat in htmlfeaturefuns:
            vd = feat.extract(stack)              
            htmlf.update(vd)                                  

        if build_token_index:
            tokenization, tokenstart, tokenend = tok.positioned_tokenize(node.string)        
            node_index[node] = (tokenstart, tokenend)
        else:
            tokenization = tok.tokenize(node.string)

        for t in tokenization:
            # 'word' needed internally, but only used externally if feature extractor
            # asks for it
            tokenf = {'word': (t.lower(), '1')} 
            for feat in tokenfeaturefuns:
                vd = feat.extract(t)
                tokenf.update(vd)
            labels.append(label)
            tokens.append((tokenf, htmlf, node, blocknr))
    return (tokens, labels, node_index)

class BlockFeatureFunction:
    # Feature extraction function returns a dictionary where the key is the featurename and the value
    # is a pair where the first part is the featurename-specifier and the other is the value 
    # E.g. {'word': ('remarkable', '1')} will turn into 'word(t)=remarkable : 1'
    def extract(input):
        pass

    def feature_names():
        pass


class Descendants(BlockFeatureFunction):
    def extract(self, stack):
        limit=len(stack) 
        parentnames=[]    
        if limit>0 and stack[0].name:
            parentnames.append(stack[0].name)
        else:
            parentnames.append('na')
        if limit>1 and stack[1].name:
            parentnames.append(stack[1].name)
        else:
            parentnames.append('na')
        if limit >2 and stack[2].name:
            parentnames.append(stack[2].name)
        else:
            parentnames.append('na')
        # print "-".join(map(lambda x: x.name,  stack))
        classname,  classlong,  classbrief=class_features(stack[0])    
        descends="-".join(map(lambda x: x.name, stack))        
        return {'parentname': (parentnames[0], '1'),  'grandparentname': (parentnames[1], '1'),  'greatgrandparentname': (parentnames[2], '1'),'classname': (classname, '1'), 'classlong': (classlong, '1'), 'classbrief': (classbrief, '1'), 'descendants': (descends, '1')}
    
    def feature_names(self):
        return ['parentname', 'grandparentname', 'greatgrandparentname','classname', 'classlong', 'classbrief', 'descendants']

class Ortho(BlockFeatureFunction):
    namemap = {'a': 'lowercase', 'A': 'capital', '1': 'number', '#': 'splchar'}

    @staticmethod
    def generalisation(token):
        # print "t: %s" % token
        alphareg=re.compile('\w', re.UNICODE)
        numreg=re.compile('[0-9]', re.UNICODE)
        long=[]
        for i in range(len(token)):
            if re.match(alphareg, token[i]):
                if re.match(numreg, token[i]):
                    long.append('1')
                elif token[i].isupper():
                    long.append('A')
                else:
                    long.append('a')
            else:
                long.append('#')
        brief=[]; 
        if len(long) > 0:
          temp=long[0]    
          for i in range(len(long)):        
              if not temp== long[i]:
                  brief.append(temp)
                  temp=long[i]
          brief.append(temp)     
        long=''.join(long)
        brief=''.join(brief)
        return long, brief

    @staticmethod         
    def countletters(tlong):
        counts = collections.defaultdict(int)
        for c in tlong:
            counts[c] += 1
        return counts


    def __init__(self):
        self._feature_nm = ['word', 'long', 'brief']
        self._feature_nm.extend(map(lambda s: s+"count", Ortho.namemap.values()))
        self._feature_nm.extend(map(lambda s: "has" + s, Ortho.namemap.values()))

    def extract(self, token):
        tlong, tbrief = Ortho.generalisation(token);
        chartypecounts = Ortho.countletters(tlong);

        ret = {'long': (tlong, '1') ,'brief': (tbrief, '1') }
        for k in Ortho.namemap.keys():
            ret["%scount" % Ortho.namemap[k]] = ('', str(chartypecounts[k])) 
            ret["has%s" % Ortho.namemap[k]] = ('', str(int(chartypecounts[k] > 0)))

        return ret 
    
    def feature_names(self):
        return self._feature_nm
    

def nodeblocks(retfile, tokens, filterf):
    c = 0
    curnode = tokens[0][2]

    # Gather the nodes that have non-O tags
    curtags = []
    curfilterstat = False;

    for line in retfile:
        if line == "\n":
            continue
        if not curnode is tokens[c][2]:
            if curfilterstat:
                yield (curnode, curtags)
            curtags = []
            curnode = tokens[c][2]
            curfilterstat = False;        
        parts = line.split("\t")
        tag = parts[-1].strip()
        curtags.append(tag)
        curfilterstat = curfilterstat or filterf(tag)
        c += 1
    if curfilterstat:
        yield (curnode, curtags)

    # Check that lengths match
    assert(c == len(tokens))


            

def sentence_split(tokens):
    ltemp = []
    if len(tokens) > 0:
        curblock = tokens[0][3]
    for t in xrange(len(tokens)):        
        ltemp.append(tokens[t])
        if '.' in tokens[t][0]['word'] or (t+1 < len(tokens) and tokens[t+1][3] != curblock):
            yield(ltemp)
            ltemp = []            
            if t+1 < len(tokens):
                curblock = tokens[t+1][3]
    if len(ltemp) > 0:
        yield(ltemp)

def write_feature_line(featurenames, tokenfeat, timesuffix):
    return "\t".join(["%s%s%s%s : %s" % (f, timesuffix, '=' if len(tokenfeat[f][0]) > 0 else '', tokenfeat[f][0], tokenfeat[f][1]) for f in featurenames if tokenfeat.has_key(f)])

def window(start, end, t, sent, featurenames, featgroup):
    s = write_feature_line(featurenames, sent[t][featgroup], "(t)")
    for i in [k for k in range(start, end+1) if k!=0]:
        if i < 0:
            toffset = "%d" % i
        else:
            toffset = "+%d" % i
        timesuffix = "(t%s)" % toffset
        if t+i >= 0 and t+i < len(sent) - 1:
            s += "\t" + write_feature_line(featurenames, sent[t+i][featgroup], timesuffix)
    return s

def parse_feature_set_desc(s):
    featuregroups = s.split("+")
    try:
        ret = map(lambda st: re.match("([a-z]+)([0-9])", st).groups(), featuregroups)
        ret = map(lambda x: (x[0], int(x[1])), ret)
        return ret
    except AttributeError:
        raise ValueError("'%s' is not a valid feature set description" % s)

def feature_set_to_feature_function(parsed_feature_set):
    feature_set_descr = []
    htmlfeaturefuns = []
    tokenfeaturefuns = []
    for feature_name, window_size in parsed_feature_set:
        if feature_name == "ortho":
            blockf = Ortho()
            tokenfeaturefuns.append(blockf)
            feature_set_descr.append((feature_name, window_size, blockf, (0, len(tokenfeaturefuns) - 1)))
        elif feature_name == "html":
            blockf = Descendants()
            htmlfeaturefuns.append(blockf)
            feature_set_descr.append((feature_name, window_size, blockf, (1, len(htmlfeaturefuns) - 1)))
    return (htmlfeaturefuns, tokenfeaturefuns, feature_set_descr)

def preprocess_file(page, feature_set, build_node_index=False):        
    nodes = []

    parsed_feature_set = parse_feature_set_desc(feature_set)
    htmlfeaturefuns, tokenfeaturefuns, feature_set_descr = feature_set_to_feature_function(parsed_feature_set)

    nodelist = htmlparse(page)

    tokens, tags, node_index = traverse_html_nodes(nodelist, htmlfeaturefuns, tokenfeaturefuns, build_node_index)            

    words=[]; f_ortho1=[]; f_ortho3=[]; f_html=[]; labels=[]
    sentences = []

    print "Page tokens"
    print len(tokens), len(tags)
    c = 0
    sentencec = 0

    for sent in sentence_split(tokens):
        for t in range(len(sent)):
            words.append(sent[t][0]["word"][0])
            
            line = []
            for feature_name, window_size, blockfeaturef, feature_addr in feature_set_descr: 
                if window_size == 1:
                    wstart = 0
                    wend = 0
                else:
                    wstart = -(window_size // 2);
                    wend = window_size // 2;
                line.append(window(wstart, wend, t, sent, blockfeaturef.feature_names(), feature_addr[0]))
                
            sentences.append("\t".join(line))

            labels.append(tags[c])
            c += 1
        sentencec += 1
        words.append('\n'); f_ortho1.append('\n'); f_ortho3.append('\n'); f_html.append('\n'); labels.append('\n'); sentences.append('\n')   


    print "Tokens after sentence split"
    print len(sentences), len(words),  len(f_ortho1),  len(f_ortho3),  len(f_html),  len(labels) 
    print len(tokens) + sentencec 
    assert(len(tokens) + sentencec == len(sentences))

    return words, f_ortho1,  f_ortho3, f_html, labels, sentences, nodes, node_index, tokens
