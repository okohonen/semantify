
0. Introduction

This is the preliminary readme file for scripts employed to obtain the experimental 
results for the conditional random field model described in the paper 
'Local Perceptron Training of Conditional Random Fields'.


1. Model training and application

Example model training and application for shallow parsing on a subset of CoNLL-2000 (freely available at http://www.cnts.ua.ac.be/conll2000/chunking/):

./run.sh conll2000 chunking-bio first-order-chain perceptron exact


2. Data format

Corpus files should be formatted as a word form and corresponding tags on one line with empty lines indicating instance boundary:

word-form\tTAG\tTAG
word-form\tTAG\tTAG

word-form\tTAG\tTAG
word-form\tTAG\tTAG

See also to the example files based on the CoNLL-200 data (freely available at http://www.cnts.ua.ac.be/conll2000/chunking/) in ./data/CoNLL-2000 directory. 


3. Libraries

External libraries required:

- Numerical Python (NumPy)
