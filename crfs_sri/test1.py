
import string
import re
import os
from bs4 import BeautifulSoup as Soup
from bs4 import NavigableString
import devutil
import time

filename='snippetfile'

page=open(os.getcwd()+'/temp/'+filename+'.html','r')

soup=Soup(page)

for i in soup.body.descendants:           
 if isinstance(i,NavigableString):                
  if len(i)<50 and len(i)>2:
   print i
   print i.parent.name
	



