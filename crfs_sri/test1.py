
import string
import re
import os
from bs4 import BeautifulSoup as Soup
from bs4 import NavigableString
import devutil
import time
from sklearn.metrics import confusion_matrix
import numpy
import sqlite3

path='/data/amazon/'
filename='amazon052'
tagindex=20
tagset=['genre','item', 'price', 'stock', 'features']
tagdict=['WebAnnotator_genre\nWebAnnotator_item\nWebAnnotator_price"\n"WebAnnotator_stock"\n"WebAnnotator_features']

#tag=open(os.getcwd()+'/data/application/temp/file_20131025_182137.train')

text='word(t)=Finland : 1	iscapital : 1	isnumber : 0	hasnumber : 0	hassplchars : 0	longcurrent(t)=Aaaaaaa : 1	briefcurrent(t)=Aa : 1	previousterm(t)=CentralNotice : 1longprevious(t)=AaaaaaaAaaaaa : 1	briefprevious(t)=AaAa : 1	nextterm(t)=From : 1	longnext(t)=Aaaa : 1	briefnext(t)=Aa : 1	classname(t)=na : 1	classlong(t)=A : 1	classbrief(t)=B : 1	parentname(t)=span : 1	grandparentname(t)=h1 : 1	greatgrandparentname(t)=div : 1	ancestors(t)=span-h1-div-body : 1	O'


print text.split(' : ')
