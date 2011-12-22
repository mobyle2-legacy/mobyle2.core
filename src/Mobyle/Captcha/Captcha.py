############################################################################################
#                                                                                          #
# The code below is from the pycaptcha-0.4 package ( http://releases.navi.cx/pycaptcha/ )  #
# Copyright (c) 2004 Micah Dowty  (see COPYING in this directory for further details )     #                     #
# and adapted by Bertrand Neron, for the purpose of Mobyle                                 #                     #
#                                                                                          #
############################################################################################

import random, string, time
import Image
from Mobyle.Captcha import Words , Backgrounds , Text , Distortions

def randomIdentifier(alphabet = string.ascii_letters + string.digits,
                     length = 24):
    return "".join([random.choice(alphabet) for i in xrange(length)])


class PseudoGimpy():
    """A relatively easy CAPTCHA that's somewhat easy on the eyes
       The render() function generates the CAPTCHA image at the given size by
       combining Layer instances from self.layers.
       """
    minCorrectSolutions = 1
    maxIncorrectSolutions = 0   
    defaultSize = (256,96)
  
    def __init__(self):
        self.solutions = []
        self.valid = True

        # Each test has a unique identifier, used to refer to that test
        # later, and a creation time so it can expire later.
        self.id = randomIdentifier()
        self.creationTime = time.time()

        self._layers = self.getLayers()
    
    def addSolution(self, solution):
        self.solutions.append(solution)

    def testSolutions(self, solutions):
        """Test whether the given solutions are sufficient for this CAPTCHA.
           A given CAPTCHA can only be tested once, after that it is invalid
           and always returns False. This makes random guessing much less effective.
           """
        if not self.valid:
            return False
        self.valid = False

        numCorrect = 0
        numIncorrect = 0

        for solution in solutions:
            if solution in self.solutions:
                numCorrect += 1
            else:
                numIncorrect += 1

        return numCorrect >= self.minCorrectSolutions and \
               numIncorrect <= self.maxIncorrectSolutions

    def getImage(self):
        """Get a PIL image representing this CAPTCHA test, creating it if necessary"""
        if not self._image:
            self._image = self.render()
        return self._image


    def getLayers(self):
        word = Words.defaultWordList.pick()
        self.addSolution(word)
        return [
            random.choice([
                Backgrounds.CroppedImage(),
                Backgrounds.TiledImage(),
            ]),
            Text.TextLayer(word, borderSize=1),
            Distortions.SineWarp(),
            ]

    def render(self, size=None):
        """Render this CAPTCHA, returning a PIL image"""
        if size is None:
            size = self.defaultSize
        img = Image.new("RGB", size)
        return self._renderList(self._layers, Image.new("RGB", size))

    def _renderList(self, l, img):
        for i in l:
            if type(i) == tuple or type(i) == list:
                img = self._renderList(i, img)
            else:
                img = i.render(img) or img
        return img





    
