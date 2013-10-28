
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
tagdict=['WebAnnotator_genre', 'WebAnnotator_item', 'WebAnnotator_price', 'WebAnnotator_stock', 'WebAnnotator_features']

tag=open(os.getcwd()+'/data/application/temp/file_20131025_182137.train')

#text="word(t)=features : 1	iscapital : 0	isnumber : 0	hasnumber : 0	hassplchars : 0longcurrent(t)=aaaaaaaa : 1	briefcurrent(t)=a : 1	previousterm(t)=stock : 1	longprevious(t)=aaaaa : 1	briefprevious(t)=a : 1	nextterm(t)=Cancel : 1	longnext(t)=Aaaaaa : 1	briefnext(t)=Aa : 1		classname(t)='WebAnnotator_features id' : 1	classlong(t)=#AaaAaaaaaaaa#aaaaaaaa#aa# : 1	classbrief(t)=#AaAa#a#a# : 1	parentname(t)=button : 1	grandparentname(t)=div : 1	greatgrandparentname(t)=div : 1	ancestors(t)=button-div-div-body : 1"

for text in tag.read().splitlines():
    print text.split(' : ')
    

