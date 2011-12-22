########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

import unittest2 as unittest
import os 
import sys
import shutil
import glob
import random


MOBYLEHOME = os.path.abspath( os.path.join( os.path.dirname( __file__ ) , "../../../../" ) )
os.environ[ 'MOBYLEHOME' ] = MOBYLEHOME
if ( MOBYLEHOME ) not in sys.path:
    sys.path.append( MOBYLEHOME )
if ( os.path.join( MOBYLEHOME , 'Src' ) ) not in sys.path:    
    sys.path.append( os.path.join( MOBYLEHOME , 'Src' ) )
    
DATADIR = os.path.dirname( __file__ )

import Mobyle.Test.MobyleTest 
from Mobyle.Converter import squizz_sequence
from Mobyle.MobyleError import MobyleError , UnSupportedFormatError

squizz_path = Mobyle.Test.MobyleTest.find_exe( "squizz" )

class SquizzSequenceTest(unittest.TestCase):
    
    def __init__(self , methodName='runTest'):
        unittest.TestCase.__init__( self , methodName = methodName )
        self.s = squizz_sequence(squizz_path)
        
    @unittest.skipUnless( squizz_path , "squizz executable not found" )    
    def setUp(self):
        self.supportedFormats =  [ 'SWISSPROT' , 'EMBL' , 'GENBANK' , 'PIR' , 'NBRF' , 
                                  'GDE' , 'IG' , 'FASTA' , 'GCG' , 'RAW' ]
        self.supportedFormats.sort( )
        self.cfg = Mobyle.ConfigManager.Config()
        shutil.rmtree( self.cfg.test_dir , ignore_errors=True )
        os.makedirs( self.cfg.test_dir )

    def tearDown(self):
        shutil.rmtree( self.cfg.test_dir , ignore_errors=True )
        
    def testDetectedFormat(self):
        detectedFormat = self.s.detectedFormat()
        detectedFormat.sort()
        self.assertEqual( detectedFormat , self.supportedFormats )
        
    def testConvertedFormat(self):
        conversions = []
        formats = self.supportedFormats
        for inputFormat in formats:
            for outputFormat in formats:
                conversions.append( ( inputFormat , outputFormat) )
        conversions.sort()
        conversionAllowed = self.s.convertedFormat()
        conversionAllowed.sort()
        self.assertEqual( conversions , conversionAllowed )
        
    def testDetect(self):
        #test of detected format
        sequence_files = glob.glob( os.path.join( DATADIR , 'DataSequences/sequence.*' ) )
        for sequence_file in sequence_files:
            format = os.path.splitext( sequence_file )[1][1:]
            converter_format , converter_number = self.s.detect( sequence_file )
            self.assertEqual( converter_format , format )
            self.assertEqual( converter_number , 1 )
        #test the number of entries in a file   
        fh = open( os.path.join( DATADIR , "DataSequences/sequence.FASTA" ) )
        fasta = ''.join( fh.readlines() )
        fh.close()
        n = random.randint( 1 , 5 )
        fastan = fasta +'\n'
        fastan = fastan * n
        fileName = os.path.join( self.cfg.test_dir , 'sequence.fasta' )
        fh = open( fileName , 'w' )
        fh.write( fastan )
        fh.close()
        converter_format , converter_number = self.s.detect( fileName )
        self.assertEqual( converter_number , n )    
        #test with a non sequence file
        fh = open( os.path.join( DATADIR ,"DataSequences/sequence.SWISSPROT" ) )
        sp = fh.readlines() 
        fh.close()
        random.shuffle( sp )
        sp = ''.join( sp )
        fileName = os.path.join( self.cfg.test_dir , 'sequence.unkn' )
        fh = open( fileName , 'w' )
        fh.write( sp )
        fh.close()
        converter_format , converter_number = self.s.detect( fileName )
        self.assertEqual( converter_format , None )
        self.assertEqual( converter_number , None )
        
    def testConvert(self):    
        sequence_files = glob.glob( os.path.join( DATADIR , 'DataSequences/sequence.*' ) )
        for srcFileName in sequence_files:
            destFileName = os.path.join( self.cfg.test_dir , os.path.basename( srcFileName ) ) +'.ori'
            shutil.copyfile( srcFileName , destFileName )
            fmtIn = os.path.splitext( destFileName[ :-4] )[1][1:]
            convertedFileName = self.s.convert( destFileName , fmtIn , fmtIn )
            converter_format , _ = self.s.detect( convertedFileName )
            self.assertEqual( converter_format , fmtIn )
        destFileName = os.path.join( self.cfg.test_dir , 'sequence.SWISSPROT' )    
        self.assertRaises( UnSupportedFormatError , self.s.convert , destFileName , "anything" )
        self.assertRaises( UnSupportedFormatError , self.s.convert , destFileName , "FASTA" , "anything" )
        self.assertRaises( MobyleError , self.s.convert , destFileName , "FASTA" , "GDE" )
    
if __name__ == '__main__':
    import logging
    mobyle = logging.getLogger('Mobyle')
    defaultHandler = logging.FileHandler( '/dev/null' , 'a' )
    mobyle.addHandler( defaultHandler  )
    unittest.main()
