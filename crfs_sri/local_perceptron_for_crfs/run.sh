#!/bin/bash

corpus=$1
task=$2
graph=$3
algorithm=$4
inference=$5
toy=$6

#echo
#echo "corpus: " $corpus
#echo "task: " $task
#echo "algorithm: " $algorithm
#echo "toy: " $toy
#echo

echo "python run.py --corpus ${corpus} --task ${task} --graph ${graph} --inference ${inference} --train_algorithm ${algorithm} --train_file ${toy}data/${corpus}/${corpus}.train --devel_file ${toy}data/${corpus}/${corpus}.devel --devel_prediction_file predictions/${corpus}.${task}.${algorithm}.${inference}.devel.prediction --model_file models/${corpus}.${task}.${algorithm}.${inference}.model --test_file ${toy}data/${corpus}/${corpus}.test --test_prediction_file predictions/${corpus}.${task}.${algorithm}.${inference}.test.prediction --test_reference_file ${toy}data/${corpus}/${corpus}.test.reference --verbose"

python run.py --graph ${graph} --train_algorithm ${algorithm} --inference ${inference} --corpus ${corpus} --task ${task} --train_file ${toy}data/${corpus}/${corpus}.train --devel_file ${toy}data/${corpus}/${corpus}.devel --devel_prediction_file predictions/${corpus}.${task}.${algorithm}.${inference}.devel.prediction --model_file models/${corpus}.${task}.${algorithm}.${inference}.model --test_file ${toy}data/${corpus}/${corpus}.test --test_prediction_file predictions/${corpus}.${task}.${algorithm}.${inference}.test.prediction --test_reference_file ${toy}data/${corpus}/${corpus}.test.reference --verbose 

#python train.py --graph ${graph} --train_algorithm ${algorithm} --inference ${inference} --corpus ${corpus} --task ${task} --train_file ${toy}data/${corpus}/${corpus}.train --devel_file ${toy}data/${corpus}/${corpus}.devel --prediction_file predictions/${corpus}.${task}.${algorithm}.${inference}.devel.prediction --model_file models/${corpus}.${task}.${algorithm}.${inference}.model --verbose 
#python apply.py --model_file models/${corpus}.${task}.${algorithm}.${inference}.model --test_file ${toy}data/${corpus}/${corpus}.test --prediction_file predictions/${corpus}.${task}.${algorithm}.${inference}.test.prediction --reference_file ${toy}data/${corpus}/${corpus}.test.reference --verbose 




