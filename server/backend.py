#! /usr/bin/env python

import sys
import os
from datetime import datetime
import semantify
import shlex, subprocess


#   Starting server
#fileserver()

#   Opening error log 
errorlog=open(os.getcwd()+'/temp/errorlog.txt',  'wb')
successlog=open(os.getcwd()+'/temp/successlog.txt',  'wb')

#   Processing requests incessantly.....

while True:
    try:
        filename='livescorenone'
        
        #filename              =os.getcwd()+'/'+filename+'.html'
        trainfile               =os.getcwd()+'/temp/'+filename+'.train'
        #os.environ['trainfile'] = trainfile
        traindevelfile       =os.getcwd()+'/temp/'+filename+'.train.devel'
        testfile                 =os.getcwd()+'/temp/'+filename+'.test'
        testdevelfile         =os.getcwd()+'/temp/'+filename+'.test.devel'
        segmentationfile =os.getcwd()+'/temp/'+filename+'.segmentation' 
        clientmodel         =os.getcwd()+'/temp/'+filename+'.model'
        
        value=semantify.receive_file(filename)
        if value==1:
            value=0
            value=semantify.preprocess(filename)
            if value==1:
                value=0
                value=semantify.develparse(filename)
                if value==1:
                    command='python ../crfs_morph/train.py --train_file %s --devel_file %s --model_file %s --verbose' % (trainfile,traindevelfile,  clientmodel)
                    args = shlex.split(command)
                    process=subprocess.Popen(args)
                    process.wait() 
                    command='python ../crfs_morph/apply.py --model_file %s --test_file %s --prediction_file %s --verbose' % (clientmodel,testfile, segmentationfile)
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
        #print 'Processing Complete for filename', filename, str(datetime.now())
