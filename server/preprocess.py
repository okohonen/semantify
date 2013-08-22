#!/usr/bin/python



#		Usage:

#		python preprocessing.py -i INPUTFILENAME  --->  filename understood to be *.html , so do not include the extension




import os
import re
import string
from bs4 import BeautifulSoup as Soup


if __name__ == "__main__":
    
    def preprocess(filename):      
        host = 'localhost'
        port = 50001
        size = 4096
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host,port)) 
        
        sock.send(filename)
        f = open(os.getcwd()+'/temp/'+filename+'.test','w')
        d = open(os.getcwd()+'/temp/'+filename+'.test.devel','w')
        filename=open(os.getcwd()+'/temp/'+filename+'.html','r') 
        soup=Soup(filename) 
        char=re.escape(string.punctuation)  
        counter=0
        tokens=[]
        alltext=soup.find_all(text=True)    
        sock.send('PUT') 
        
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
            ####### Code to add token to database
            sock.send(i)
            data=sock.recv(size) 
                        
        f.close()
        d.close()
        sock.send('DoneSendingTokens')
        data=sock.recv(size)
        if data==404:
            sock.close()    
        
        #print '\n\tinput file\t\t:' ,filename+'.html'
        #print '\ttest file\t\t:' ,filename+'.test'
        #print '\ttest.devel file\t\t:', filename+'.test.devel'
        
        return 1
