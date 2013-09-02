
import string
import os
import re


filename='snippetfile'

retfile=open(os.getcwd()+'/temp/'+filename+'.test.prediction')
a=retfile.read().splitlines()        
reg=re.compile('[A-Z]')
for terms in a:
	if terms: 
		token=terms.split(' : ')	
		token[0]=token[0].replace('word(t)=', '')            
      		token[1]=token[1].replace('1\t', '') 
		tokensplit=token[0].split()				
		char=list(tokensplit[0])				
    		if  re.match('[A-Z]', char[0]) :
			return True    	    	
    		else:
			return False
		
