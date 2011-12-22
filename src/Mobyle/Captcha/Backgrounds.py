############################################################################################
#                                                                                          #
# The code below is from the pycaptcha-0.4 package ( http://releases.navi.cx/pycaptcha/ )  #
# Copyright (c) 2004 Micah Dowty  (see COPYING in this directory for further details )     #                     #
# and adapted by Bertrand Neron, for the purpose of Mobyle                                 #                     #
#                                                                                          #
############################################################################################

import random
import Image
from Mobyle.Captcha import Pictures

class TiledImage(object):
    """Pick a random image and a random offset, and tile the rendered image with it"""
    def __init__(self, imageFactory=Pictures.abstract):
        self.tileName = imageFactory.pick()
        self.offset = (random.uniform(0, 1),
                       random.uniform(0, 1))

    def render(self, image):
        tile = Image.open(self.tileName)
        for j in xrange(-1, int(image.size[1] / tile.size[1]) + 1):
            for i in xrange(-1, int(image.size[0] / tile.size[0]) + 1):
                dest = (int((self.offset[0] + i) * tile.size[0]),
                        int((self.offset[1] + j) * tile.size[1]))
                image.paste(tile, dest)


class CroppedImage(object):
    """Pick a random image, cropped randomly. Source images should be larger than the CAPTCHA."""
    def __init__(self, imageFactory=Pictures.nature):
        self.imageName = imageFactory.pick()
        self.align = (random.uniform(0,1),
                      random.uniform(0,1))

    def render(self, image):
        i = Image.open(self.imageName)
        image.paste(i, (int(self.align[0] * (image.size[0] - i.size[0])),
                        int(self.align[1] * (image.size[1] - i.size[1]))))
