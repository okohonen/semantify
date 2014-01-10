import SimpleHTTPServer
import SocketServer
import json
import os
import string
import semantify_local
import sqlite3, shlex, subprocess,  sys,  re,  time
from bs4 import BeautifulSoup as Soup
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
# tokens, labels = semantify_local.htmlparse(fp,  htmlfeaturefuns, tokenfeaturefuns)

words, f_ortho1,  f_ortho3, f_html, labels, sentences, nodes=semantify_local.preprocess_file(fp)

devutil.keyboard()

  
