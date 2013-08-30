
0. Introduction

This is the anonymized readme file for scripts employed to obtain the experimental 
results for the conditional random field model described in paper 
'Supervised Morphological Segmentation Using Conditonal Random Fields'.


1. Model training and application

Example model training for English:

python train.py --graph first-order-chain --performance_measure accuracy --train_file toydata/wsj/wsj.train --devel_file toydata/wsj/wsj.devel --devel_prediction_file predictions/wsj.first-order-chain.devel --model_file models/wsj.first-order-chain.model --verbose

Example segmentation using the trained model: 

python apply.py --model_file models/wsj.first-order-chain.model --test_file toydata/wsj/wsj.test --test_prediction_file predictions/wsj.first-order-chain.test.prediction --test_reference_file toydata/wsj/wsj.test.reference --verbose


2. Data format

Corpus files should be formatted as one word form per line:

word-form\tsegmentation1,segmentation2,...,segmentationN

See also to the example files in ./data directory. 
The data files are preprocessed versions of the Morpho Challenge 2010 
data sets (available at http://research.ics.aalto.fi/events/morphochallenge/).


3. Libraries

External libraries included:

- Munkres package by Brian Clapper (see the documentation within file munkres.py)

External libraries required:

- Munkres
- Numerical Python (NumPy)
