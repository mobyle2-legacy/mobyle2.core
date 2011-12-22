############################################################################################
#                                                                                          #
# The code below is from the pycaptcha-0.4 package ( http://releases.navi.cx/pycaptcha/ )  #
# Copyright (c) 2004 Micah Dowty  (see COPYING in this directory for further details )     #                     #
# and adapted by Bertrand Neron, for the purpose of Mobyle                                 #                     #
#                                                                                          #
############################################################################################

import random , math 
import Image

class SineWarp(object):
    """Warp the image using a random composition of sine waves
       define a function that maps points in the output image to points in the input image.
       This warping engine runs a grid of points through this transform and uses
       PIL's mesh transform to warp the image.
       """
    filtering = Image.BILINEAR
    resolution = 10

    def __init__(self,
                 amplitudeRange = (3, 6.5),
                 periodRange    = (0.04, 0.1),
                 ):
        
        self.amplitude = random.uniform(*amplitudeRange)
        self.period = random.uniform(*periodRange)
        self.offset = (random.uniform(0, math.pi * 2 / self.period),
                       random.uniform(0, math.pi * 2 / self.period))
        
        
    def getTransform(self, image):
        return (lambda x, y,
                a = self.amplitude,
                p = self.period,
                o = self.offset:
                (math.sin( (y+o[0])*p )*a + x,
                 math.sin( (x+o[1])*p )*a + y))

    def render(self, image):
        r = self.resolution
        xPoints = image.size[0] / r + 2
        yPoints = image.size[1] / r + 2
        f = self.getTransform(image)

        # Create a list of arrays with transformed points
        xRows = []
        yRows = []
        for j in xrange(yPoints):
            xRow = []
            yRow = []
            for i in xrange(xPoints):
                x, y = f(i*r, j*r)

                # Clamp the edges so we don't get black undefined areas
                x = max(0, min(image.size[0]-1, x))
                y = max(0, min(image.size[1]-1, y))

                xRow.append(x)
                yRow.append(y)
            xRows.append(xRow)
            yRows.append(yRow)

        # Create the mesh list, with a transformation for
        # each square between points on the grid
        mesh = []
        for j in xrange(yPoints-1):
            for i in xrange(xPoints-1):
                mesh.append((
                    # Destination rectangle
                    (i*r, j*r,
                     (i+1)*r, (j+1)*r),
                    # Source quadrilateral
                    (xRows[j  ][i  ], yRows[j  ][i  ],
                     xRows[j+1][i  ], yRows[j+1][i  ],
                     xRows[j+1][i+1], yRows[j+1][i+1],
                     xRows[j  ][i+1], yRows[j  ][i+1]),
                    ))

        return image.transform(image.size, Image.MESH, mesh, self.filtering)


