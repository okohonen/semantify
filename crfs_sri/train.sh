#!/bin/bash

echo "corpus" $1
echo "task" $2
echo "train algorithm" $3

python train.py --train_file $4data/$1.train --devel_file $4data/$1.devel --tagged_devel_file tagged/$1.devel.$2.$3.tagged --model_file models/$1.$2.$3.model --verbose --corpus $1 --task $2 --train_algorithm $3