#!/usr/bin/python


#		Usage:

#		python mykeywordtagger.py -i INPUTFILENAME  --->  filename understood to be *.html , so do not include the extension



import urllib
import os
import re
import string
import time
from bs4 import BeautifulSoup as Soup
from bs4 import NavigableString
from optparse import OptionParser


parser = OptionParser("Usage: %prog [options]")
parser.add_option("--infile","--i", default = None)
parser.add_option("--outfile", "--o", default = None)

(options, args) = parser.parse_args()

starttime=time.time()
# Reference snippet to apply return tags to the html file
page=open(os.getcwd()+'/'+options.infile+'.html')
ret=open(os.getcwd()+'/temp.html','w')


soup=Soup(page)

# The keywords that need to be tagged

retfile=open(os.getcwd()+'/'+options.infile+'.segmentation')
a=retfile.read().splitlines()
tokens=[]
for terms in a:
	temptoken=terms.split('\t')
	if not temptoken[0]==temptoken[1]:
		tokens.append(temptoken)   

#b=['Cup','club','English','football','Manchester','Martino']
#newtag=i[:start]+'<a style="color:#000000; background-color:#40E0D0;" title='+b[1]+'>'+b[0]+'</a>'+i[end:]

		
# This chunk of code checks through the descendants for presence of NavigableStrings and replaces the string with an 'a' with title=keyword for tooltip purpose.
w=soup

for b in tokens:
 for child in w.descendants:
  if child.next_sibling:
   for i in child.next_sibling:				
    if isinstance(i,NavigableString):
     if len(i)<50 and len(i)>2:     
      reg=re.compile(b[0], re.IGNORECASE)      
      if b[0] in i and len(b[0])>2:
       if i.parent.name=='a':
        i.parent['title']=b[1]; i.parent['style']="color:#000000; background-color:#40E0D0"
       else:      		  
        match=re.search(reg,i)
        start, end = match.start(), match.end()      				
        newtag=i[:start]+'<span style="color:#000000; background-color:#40E0D0" title="'+b[1]+'">'+b[0]+'</span>'+i[end:]				
        i.string.replace_with(newtag)
   
   

lt='&lt;' ; gt='&gt;'

for i in soup:		
	ret.write(repr(i))

page.close()
ret.close()

# Since Beautifulsoup uses unicode, work around here is opening the temp file and replacing the tags with appropriate '<','>' and saving the file.

fin = open(os.getcwd()+'/temp.html')
fout = open(os.getcwd()+'/'+options.infile+'tagged.html', 'wt')
for line in fin:
    if lt in line or gt in line:
	line=line.replace('&lt;','<')    
	line=line.replace('&gt;','>')
    fout.write(line)
fin.close()
fout.close()

#print 'Time elapsed is', time.time()-starttime, 'seconds'

print '\n\t\tInput file\t\t:', options.infile+'.html'
print '\t\tTagged file\t\t:', options.infile+'tagged.html'



