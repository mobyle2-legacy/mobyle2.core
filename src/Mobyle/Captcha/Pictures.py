############################################################################################
#                                                                                          #
# The code below is from the pycaptcha-0.4 package ( http://releases.navi.cx/pycaptcha/ )  #
# Copyright (c) 2004 Micah Dowty  (see COPYING in this directory for further details )     #                     #
# and adapted by Bertrand Neron, for the purpose of Mobyle                                 #                     #
#                                                                                          #
############################################################################################

import os, random , glob


class ImageFactory(object):
    """Given a list of files and/or directories, this picks a random file.
       Directories are searched for files matching any of a list of extensions.
       Files are relative to our data directory plus a subclass-specified base path.
       """
    extensions = [".png"]
    picturesPath = os.path.abspath(os.path.join(os.path.dirname(__file__), "data" , "pictures" ) )
    
    def __init__(self, image_category ):
        self.image_category = image_category
        self._fullPaths = None


    def _findFullPaths(self):
        """From our given file list, find a list of full paths to files"""
        return glob.glob( os.path.join( self.picturesPath , self.image_category , '*.png' ) )

    def pick(self):
        if self._fullPaths is None:
            self._fullPaths = self._findFullPaths()
        return random.choice(self._fullPaths)
    
abstract = ImageFactory("abstract")
nature = ImageFactory("nature")