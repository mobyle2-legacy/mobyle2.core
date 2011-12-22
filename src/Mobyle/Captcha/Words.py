############################################################################################
#                                                                                          #
# The code below is from the pycaptcha-0.4 package ( http://releases.navi.cx/pycaptcha/ )  #
# Copyright (c) 2004 Micah Dowty  (see COPYING in this directory for further details )     #                     #
# and adapted by Bertrand Neron, for the purpose of Mobyle                                 #                     #
#                                                                                          #
############################################################################################

import random, os



class WordList(object):
    """A class representing a word list read from disk lazily.
       Blank lines and comment lines starting with '#' are ignored.
       Any number of words per line may be used. The list can
       optionally ingore words not within a given length range.
       """
    def __init__(self):
        self.words = None
        self.fileName = "basic-english"

    def read(self):
        """Read words from disk"""
        f = open( os.path.abspath(os.path.join(os.path.dirname(__file__), "data" , "words" , self.fileName )))
        
        self.words = []
        for line in f.xreadlines():
            line = line.strip()
            if not line:
                continue
            if line[0] == '#':
                continue
            for word in line.split():
                self.words.append(word)

    def pick(self):
        """Pick a random word from the list, reading it in if necessary"""
        if self.words is None:
            self.read()
        return random.choice(self.words)


# Define several shared word lists that are read from disk on demand

defaultWordList = WordList() 

### The End ###
