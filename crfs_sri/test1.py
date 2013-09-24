
import string
import re
import os
from bs4 import BeautifulSoup as Soup
from bs4 import NavigableString
import devutil
import time
from sklearn.metrics import confusion_matrix

containertag='word(t)=Manchester : 1	previousterm(t)=season : 1	nextterm(t)=United : 1	iscapital : 1	isnumber : 0	hasnumber : 0	hassplchars : 0	long(t)=Aaaaaaaaaa : 1	brief(t)=Aa : 1	classname(t)="WebAnnotator_home style" : 1	classlong(t)=#AaaAaaaaaaaa#aaaa#aaaaa# : 1	classbrief(t)=#AaAa#a#a# : 1	parentname(t)=span : 1	grandparentname(t)=b : 1	greatgrandparentname(t)=p : 1	ancestors(t)=span-b-p-div-div-div-body : 1	home'




temp=containertag.split(' : ')
temp[15]=temp[15].replace('1\t', '')
temp[15]=temp[15].replace('\n', '')

print temp[15]

