########################################################################################
#                                                                                      #
#   Author: Sandrine Larroude,                                                         #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################


import unittest2 as unittest
import os
import sys
import shutil
import glob

MOBYLEHOME = os.path.abspath( os.path.join( os.path.dirname( __file__ ) , "../../../../" ) )
os.environ[ 'MOBYLEHOME' ] = MOBYLEHOME
if ( MOBYLEHOME ) not in sys.path:
    sys.path.append( MOBYLEHOME )
if ( os.path.join( MOBYLEHOME , 'Src' ) ) not in sys.path:    
    sys.path.append( os.path.join( MOBYLEHOME , 'Src' ) )

DATADIR = os.path.dirname( __file__ )

import Mobyle.Test.MobyleTest 
from Mobyle.MobyleError import UnSupportedFormatError
from Mobyle.Converter import squizz_alignment

squizz_path = Mobyle.Test.MobyleTest.find_exe( "squizz" )

class SquizzAlignmentTest(unittest.TestCase):
    """Test the Squizz alignment module"""
    
    def __init__(self , methodName='runTest'):
        unittest.TestCase.__init__( self , methodName = methodName )
        self.s = squizz_alignment(squizz_path)
    
    @unittest.skipUnless( squizz_path , "squizz executable not found" )    
    def setUp(self):
        self.cfg = Mobyle.ConfigManager.Config()
        self.list = ['CLUSTAL', 'PHYLIPI', 'PHYLIPS', 'FASTA', 'MEGA', 'MSF', 'NEXUS', 'STOCKHOLM']
        shutil.rmtree( self.cfg.test_dir , ignore_errors=True )
        os.makedirs( self.cfg.test_dir )
       
    def tearDown(self):
        shutil.rmtree( self.cfg.test_dir , ignore_errors=True )     
    
    def testDetectedFormat(self):
        #detectedFormat()
        detectedF = self.s.detectedFormat()
        self.assertEqual(detectedF.sort(), self.list.sort(), "DetectedFormat not equal")
        
    def testConvertedFormat(self):
        #convertedFormat()
        conversions = []
        formats = self.list
        for inputFormat in formats:
            for outputFormat in formats:
                conversions.append( ( inputFormat , outputFormat) )

        conversionAllowed = self.s.convertedFormat()

        self.assertEqual( conversions.sort() , conversionAllowed.sort(), "ConvertedFormat not equal" )
        
    def testDetect(self):
        #detect( dataFileName )
        
        t_files = glob.glob( os.path.join(DATADIR,'DataAlignments/align.*') )
        #There are 3 files: CLUSTAL, PHYLIPI, UNKNOWN(PHYLIPI modified)
        for ali in t_files:
            format = os.path.splitext( ali )[1][1:]
            det_format , det_number = self.s.detect( ali )
            if format == "UNKNOWN":
                self.assertEqual( det_format , None, "Unknown case: detected format not ok => %s != %s" % (det_format , format)  )
                self.assertEqual( det_number , None, "Unknown case: detected number not ok" )
            else:
                self.assertEqual( det_format , format, "detected format not ok => %s != %s" % (det_format , format)  )
                self.assertEqual( det_number , 1, "detected number not ok" )
        
    def testConvert(self):
        #convert( dataFileName , outputFormat , inputFormat = None)
        
        #classic conversion
        t_file = os.path.join(DATADIR,'DataAlignments/align.PHYLIPI') 
        dst = os.path.join(self.cfg.test_dir, 'align.test')
        shutil.copyfile( t_file , dst )
        fmtIn = os.path.splitext( t_file )[1][1:]
        fmt = "CLUSTAL"
        conv_FileName = self.s.convert( dst , fmt, fmtIn )
        det_format , _ = self.s.detect( conv_FileName )
        self.assertEqual( det_format , fmt, "conversion failed")
        
        #conversion with a wrong output format
        fmt = "tester"
        self.assertRaises(UnSupportedFormatError, self.s.convert, dst, fmt, fmtIn)
        
        #conversion of a bad file
        t_file = os.path.join(DATADIR,'DataAlignments/align.UNKNOWN')
        shutil.copyfile( t_file , dst )
        self.assertRaises(UnSupportedFormatError, self.s.convert, dst, fmt, fmtIn)

      
if __name__ == '__main__':
    import logging
    mobyle = logging.getLogger('Mobyle')
    defaultHandler = logging.FileHandler( '/dev/null' , 'a' )
    mobyle.addHandler( defaultHandler  )
    unittest.main()

    
