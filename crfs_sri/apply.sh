#!/bin/bash

echo "corpus" $1
echo "task" $2
echo "train algorithm" $3

python apply.py --test_file $4data/$1.test --tagged_file tagged/$1.$2.$3.test.tagged --model_file models/$1.$2.$3.model --corpus $1 --task $2 --verbose 
