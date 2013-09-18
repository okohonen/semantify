
import string
import re
import os
from bs4 import BeautifulSoup as Soup
from bs4 import NavigableString
import devutil
import time
from sklearn.metrics import confusion_matrix

containertag='<div id="black-text">Let your voice be heard! <br/> Give your input on the draft of our new privacy policy.</div>'

token='your word is'

print [k in containertag for k in token.split()]

