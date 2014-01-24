import SimpleHTTPServer
import SocketServer
import json
import os
import string
import semantify_local
import sqlite3, shlex, subprocess,  sys,  re,  time
from bs4 import BeautifulSoup 
from bs4 import NavigableString
from datetime import datetime
import unicodedata
import numpy
import devutil
import zlib
import nltk

# Usage: ~/code/semantify/crfs_sri> python preprocess_file.py filename.html


# htmlfeaturefuns = [semantify_local.descendants]
# tokenfeaturefuns = [semantify_local.ortho]
fp = open(sys.argv[1])
#for t in semantify_local.htmlparse(fp,  htmlfeaturefuns, tokenfeaturefuns):
#    devutil.keyboard()

page = BeautifulSoup(fp)

words, f_ortho1,  f_ortho3, f_html, labels, sentences, nodes, node_index, tokens=semantify_local.preprocess_file(page, build_node_index=True)

# Build test file
# semantify_local.write_testfiles("", "Talviurheilu-KeltainenPorssi", sentences)
# Then apply: python dummy_tagger.py ../samples/Talviurheilu-KeltainenPorssi.test > ../samples/Talviurheilu-KeltainenPorssi.test.prediction
nodes_to_tag = semantify_local.extract_tagged_nodes(open(sys.argv[2]), tokens)

print nodes_to_tag

semantify_local.apply_tagging(page, nodes_to_tag, node_index)

print str(page)


  
