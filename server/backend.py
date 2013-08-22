#! /usr/bin/env python

import sys
import os
from datetime import datetime
import semantify
import shlex, subprocess


#   Opening error log 
errorlog=open(os.getcwd()+'/temp/errorlog.txt',  'wb')
successlog=open(os.getcwd()+'/temp/successlog.txt',  'wb')

# Garbage collection counter
GC=0

#   Processing requests incessantly.....

#           Note:
#           Filename to be originally got from the browser's save button click. A temp arrangement has been used below for simulation purpose.

try:
    GC=GC+1
    filename='livescorenone'
    
    #filename              =os.getcwd()+'/'+filename+'.html'
    trainfile               =os.getcwd()+'/temp/'+filename+'.train'

    traindevelfile       =os.getcwd()+'/temp/'+filename+'.train.devel'
    testfile                 =os.getcwd()+'/temp/'+filename+'.test'
    testdevelfile         =os.getcwd()+'/temp/'+filename+'.test.devel'
    segmentationfile =os.getcwd()+'/temp/'+filename+'.segmentation' 
    clientmodel         =os.getcwd()+'/temp/'+filename+'.model'
    standardmodel          =os.getcwd()+'/morphochal2010+eng.model'
    
    value=semantify.receive_file(filename)
    if value==1:
        value=0
        value=semantify.preprocess(filename)
        if value==1:
            value=0
            value=semantify.develparse(filename)
            if value==1:
                command='python train.py --train_file %s --devel_file %s --prediction_file %s --model_file %s --verbose' % (trainfile,traindevelfile, segmentationfile, clientmodel)
                args = shlex.split(command)
                process=subprocess.Popen(args)
                process.wait() 
                command='python apply.py --model_file %s --test_file %s --prediction_file %s --verbose' % (standardmodel,testfile, segmentationfile)
                args = shlex.split(command)
                process=subprocess.Popen(args)
                process.wait()      
                value=semantify.keywordtag(filename)
                if value==1:
                    value=0
                    semantify.send_file(filename)
    successlog.write(filename)
    successlog.write('\t')
    successlog.write( str(datetime.now()))
    successlog.write('\n')
    
    if GC%5==0:
        semantify.garbagecollection()
    
except Exception as e:
    errorlog.write(filename)
    errorlog.write('\t')
    errorlog.write(str(datetime.now()))
    errorlog.write('\t')
    errorlog.write(str(e))       
    errorlog.write('\n')
    raise
    
finally:
    pass
    print 'Processing Complete for filename', filename, str(datetime.now())
