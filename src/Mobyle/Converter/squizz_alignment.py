########################################################################################
#                                                                                      #
#   Author: Sandrine Larroude                                                          #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

"""
This is a squizz converter module for alignment
"""

import os, re
from subprocess import Popen , PIPE

from logging import getLogger
s_log = getLogger(__name__)

from Mobyle.MobyleError import MobyleError , UnSupportedFormatError
from Mobyle.Converter.DataConverter import DataConverter

class squizz_alignment( DataConverter ):
    
    def __init__(self , path ):
        super( squizz_alignment , self ).__init__( path )
        self.program_name = 'squizz'

    def detect( self, dataFileName ):
        """
        detect the format of the data.
        @param dataFileName: the filename of the data which the format must be detected
        @type dataFileName: string
        @return: the format of this data and the number of entry. 
               if the format cannot be detected, return None
               if the number of entry cannot be detected, return None
        @rtype: ( string format , int number of entry ) 
        """
        squizz_path = self.path
        
        if squizz_path is None:
            s_log.critical( "squizz path is not configured." )
            raise MobyleError , 'squizz is required to handle Alignment data but not configured.(See section SEQCONVERTER on Config.py)'
        
        nb, format = None, None
        try:
            squizz_pipe = Popen( [ squizz_path , "-An" , dataFileName ] ,
                                 shell = False ,
                                 stdout = None ,
                                 stdin = None ,
                                 stderr = PIPE
                                 )
        except OSError, err:
            msg = "squizz exit abnormally: " + str( err )
            s_log.critical( msg )
            raise MobyleError, msg
        
        squizz_pipe.wait()
        if squizz_pipe.returncode != 0:
            msg = ''.join( squizz_pipe.stderr.readlines() )
            match = re.search( "squizz: invalid option -n" , msg )
            if match:
                msg = "Your squizz binary is too old. Please upgrade it."
                s_log.critical( msg )
            raise MobyleError , msg
        
        for line in squizz_pipe.stderr:
            match = re.search( ": (.+) format, (\d+) entries\.$" ,  line)
            if match :
                format = match.group(1)
                nb = int( match.group(2))
                break
        
        if format == "UNKNOWN": 
            format, nb = None, None
            
        return (format, nb)
    
    def detectedFormat(self):
        """
        @return: the list of detectable formats.
        @rtype: list of strings
        """
        return [ 'CLUSTAL',
                 'PHYLIP',
                 'PHYLIPI',
                 'PHYLIPS',
                 'FASTA',
                 'MEGA',
                 'MSF',
                 'NEXUS',
                 'STOCKHOLM' 
                ]
    
    
    def convert( self, dataFileName , outputFormat , inputFormat = None):
        """
        convert a data in the format outputFormat
        @param dataFileName: the filename of the data to convert
        @type dataFileName: string
        @param outputFormat: the format in which the data must be convert in.
        @type outputFormat: string
        @param inputFormat: the format of the data 
        @type inputFormat: string
        @return: the filename of the converted data.
        @rtype: string
        @raise UnsupportedFormatError: if the outputFormat is not supported, or if the data is in unsupported format.
        """
        squizz_path =  self.path
    
        if squizz_path is None:
            s_log.critical( "squizz path is not configured." )
            raise MobyleError , 'squizz is required to handle Alignment data but not configured.(See section SEQCONVERTER on Config.py)'
    
        outFileName = os.path.splitext( dataFileName )[0] + "." + outputFormat.lower()
        try:
            outFile = open( outFileName , 'w' )
        except IOError, err :
            s_log.error( "Can't write outFile:" + str( err ) )
            raise MobyleError , "Alignment Conversion Error: "+ str( err )
        
        #number of entries is also returned but not useful
        det_format , _ = self.detect (dataFileName) 
        
        if det_format:
            #Command building
            cmde =  [ squizz_path , "-c", outputFormat ]
            if  inputFormat:
                cmde += [ "-f" , inputFormat ,
                         dataFileName    ]
            else:
                cmde.append( dataFileName )
                
            try:
                squizz_pipe = Popen( cmde ,
                                     shell  = False ,
                                     stdout = outFile ,
                                     stdin  = None ,
                                     stderr = PIPE
                                     )
            except OSError, err:
                msg = "squizz exit abnormally: " + str( err )
                s_log.critical( msg )
                raise MobyleError, msg
                
            squizz_pipe.wait()
            if squizz_pipe.returncode != 0:
                msg = ''.join( squizz_pipe.stderr.readlines() )
                match = re.search("unsupported format\.$", msg)
                if match:
                    s_log.error( msg )
                    raise UnSupportedFormatError , msg
            else:
                outFile.close()
                return outFileName
        
        else:
            # the inFormat is not recognize
            raise UnSupportedFormatError
    
    
    def convertedFormat(self):
        """
        @return: the list of allowed conversion ( inputFormat , outputFormat ) 
        @rtype: [ ( string inputFormat, string outputFormat )  , ... ]
        """
        conversions = []
        formats = self.detectedFormat()
        for inputFormat in formats:
            for outputFomat in formats:
                conversions.append( ( inputFormat , outputFomat) )
        return conversions
    
