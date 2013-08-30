#!/bin/bash

data=$1
graph=$2
performancemeasure=$3
toy=$4

#echo
#echo "corpus: " $corpus
#echo "task: " $task
#echo "algorithm: " $algorithm
#echo "toy: " $toy
#echo

echo "python run.py --graph ${graph} --performance_measure $performancemeasure --train_file ${toy}data/${data}/${data}.train --devel_file ${toy}data/${data}/${data}.devel --devel_prediction_file predictions/$data.${graph}.devel.prediction --model_file models/${data}.$graph.model --test_file ${toy}data/${data}/${data}.test --test_prediction_file predictions/${data}.${graph}.test.prediction --test_reference_file ${toy}data/${data}/${data}.test.reference --verbose"

python run.py --graph ${graph} --performance_measure $performancemeasure --train_file ${toy}data/${data}/${data}.train --devel_file ${toy}data/${data}/${data}.devel --devel_prediction_file predictions/$data.${graph}.devel.prediction --model_file models/${data}.$graph.model --test_file ${toy}data/${data}/${data}.test --test_prediction_file predictions/${data}.${graph}.test.prediction --test_reference_file ${toy}data/${data}/${data}.test.reference --verbose 





