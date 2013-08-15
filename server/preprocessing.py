#!/usr/bin/python



#		Usage:

#		python preprocessing.py -i INPUTFILENAME  --->  filename understood to be *.html , so do not include the extension




import os
import re
import string
from bs4 import BeautifulSoup as Soup
from optparse import OptionParser



parser = OptionParser("Usage: %prog [options]")
parser.add_option("--infile","--i",default = None)
#parser.add_option("--outtest","--ot",default = None)
#parser.add_option("--outtestdevel","--otd",default = None)
(options, args) = parser.parse_args()

page=open(os.getcwd()+'/'+options.infile+'.html','r')
soup=Soup(page)

char=re.escape(string.punctuation)
f = open(os.getcwd()+'/'+options.infile+'.test','w')
d = open(os.getcwd()+'/'+options.infile+'.test.devel','w')
counter=0
tokens=[]
alltext=soup.find_all(text=True)
for a in range(len(alltext)):
 	alltext[a]=re.sub('[^a-zA-Z\n\.]', ' ', alltext[a])
 	alltext[a]=re.sub(r'['+char+']', ' ',alltext[a])
 	words=alltext[a].split()
 	for i in range(len(words)): 
 		if len(words[i])<50 and len(words[i])>2:
   			tokens.append(words[i]) 

tokens=set(tokens)   
for i in tokens:
 	f.write(i+'\n')
 	counter=counter+1
 	if counter % 10 <1:
  		d.write(i+'\n')   
f.close()
d.close()

print '\n\tinput file\t\t:' ,options.infile+'.html'
print '\ttest file\t\t:' ,options.infile+'.test'
print '\ttest.devel file\t\t:', options.infile+'.test.devel'