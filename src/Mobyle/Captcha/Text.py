############################################################################################
#                                                                                          #
# The code below is from the pycaptcha-0.4 package ( http://releases.navi.cx/pycaptcha/ )  #
# Copyright (c) 2004 Micah Dowty  (see COPYING in this directory for further details )     #                     #
# and adapted by Bertrand Neron, for the purpose of Mobyle                                 #                     #
#                                                                                          #
############################################################################################

import os , glob , random
import ImageFont, ImageDraw

class FontFactory(object):
    """Picks random fonts and/or sizes from a given list.
       'sizes' can be a single size or a (min,max) tuple.
       If any of the given files are directories, all *.ttf found
       in that directory will be added.
       """
    basePath = "fonts"
    fontsPath = os.path.abspath(os.path.join(os.path.dirname(__file__), "data" , "fonts" ) )
    
    
    def __init__(self, sizes, font_category ):
        self.font_category = font_category
        self._fullPaths = None
        
        if type(sizes) is tuple:
            self.minSize = sizes[0]
            self.maxSize = sizes[1]
        else:
            self.minSize = sizes
            self.maxSize = sizes

    def _findFullPaths(self):
        """From our given file list, find a list of full paths to files"""
        return glob.glob( os.path.join( self.fontsPath , self.font_category , '*.ttf' ) )

    def pick(self):
        """Returns a (fileName, size) tuple that can be passed to ImageFont.truetype()"""
        if self._fullPaths is None:
            self._fullPaths = self._findFullPaths()
        fileName = random.choice(self._fullPaths)
        size = int(random.uniform(self.minSize, self.maxSize) + 0.5)
        return (fileName, size)
    

   
    
class TextLayer(object):
    """Represents a piece of text rendered within the image.
       Alignment is given such that (0,0) places the text in the
       top-left corner and (1,1) places it in the bottom-left.

       The font and alignment are optional, if not specified one is
       chosen randomly. If no font factory is specified, the default is used.
       """
    def __init__(self, text,
                 borderSize  = 0,
                 ):
        fontFactory = FontFactory((30, 40), "vera")
        self.font = fontFactory.pick()
        self.alignment = (random.uniform(0,1), random.uniform(0,1))
        self.text        = text
        self.textColor   = "black"
        self.borderSize  = borderSize
        self.borderColor = "white"

    def render(self, img):
        font = ImageFont.truetype(*self.font)
        textSize = font.getsize(self.text)
        draw = ImageDraw.Draw(img)

        # Find the text's origin given our alignment and current image size
        x = int((img.size[0] - textSize[0] - self.borderSize*2) * self.alignment[0] + 0.5)
        y = int((img.size[1] - textSize[1] - self.borderSize*2) * self.alignment[1] + 0.5)

        # Draw the border if we need one. This is slow and ugly, but there doesn't
        # seem to be a better way with PIL.
        if self.borderSize > 0:
            for bx in (-1,0,1):
                for by in (-1,0,1):
                    if bx and by:
                        draw.text((x + bx * self.borderSize,
                                   y + by * self.borderSize),
                                  self.text, font=font, fill=self.borderColor)

        # And the text itself...
        draw.text((x,y), self.text, font=font, fill=self.textColor)
