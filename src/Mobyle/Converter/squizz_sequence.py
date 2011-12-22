########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

"""
This module is used as template to build a converter module
"""
import os
import re
from subprocess import Popen , PIPE
from logging import getLogger
_log = getLogger( __name__ )

from Mobyle.MobyleError import MobyleError , UnSupportedFormatError
from Mobyle.Converter.DataConverter import DataConverter

class squizz_sequence( DataConverter ):
    
    def __init__(self , path ):
        super( squizz_sequence , self ).__init__( path )
        self.program_name = 'squizz'
        
        
    def suffixe( self , format ):
        return '.' + format.lower()
               
    def detect( self, dataFileName ):
        """
        detect the format of the data.
        @param dataFileName: the filename of the data which the format must be detected
        @type dataFileName: string
        @return: the format of this data. if the format cannot be detected , return None
        @rtype: string
        """
        
        if self.path is None :
            _log.critical( "squizz path is not configured" )
            raise MobyleError , 'squizz is required to handle data Sequence but not configured' 
        else:
            try:
                squizz_pipe = Popen( [ self.path , "-Sn" , dataFileName ] ,
                                     shell = False ,
                                     stdout = None ,
                                     stdin = None ,
                                     stderr = PIPE
                                     )
            except OSError , err :
                msg = "squizz exit abnormally: " + str(err)
                _log.critical( msg )
                raise MobyleError, msg
            squizz_pipe.wait()
            if squizz_pipe.returncode != 0:
                msg = ''.join( squizz_pipe.stderr.readlines() )
                match = re.search( "squizz: invalid option -- n" , msg )
                if match:
                    msg = "your squizz binary is too old. Please upgrade it"
                    _log.critical( msg )
                raise MobyleError , msg
                    
            for line in squizz_pipe.stderr :
                match = re.search( ": (.+) format, (\d+) entries\.$" ,  line)
                if match :
                    format = match.group(1)
                    seq_nb = int( match.group(2))
                    break
            if match and format != "UNKNOWN":
                return ( format , seq_nb )
            else:
                return ( None  , None )
         
    def detectedFormat(self):
        """
        @return: the list of detectables formats.
        @rtype: list of stings
        """
       
        return [ 'SWISSPROT' , 
                 'EMBL' ,
                 'GENBANK',
                 'PIR',
                 'NBRF',
                 'GDE',
                 'IG',
                 'FASTA',
                 'GCG',
                 'RAW']

        
    def convert( self , dataFileName , outputFormat , inputFormat = None ):
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
        
        outFileName = os.path.splitext( dataFileName )[0] + self.suffixe( outputFormat )
        cmde = [ self.path ,
                "-S" ,
                "-n" ,
                "-c" , outputFormat ]
        if  inputFormat:
            cmde += [ "-f" , inputFormat ,
                     dataFileName
                     ]
        else:
            cmde.append( dataFileName )
        try:
            outFile = open( outFileName , 'w' )
        except IOError ,err :
            _log.error( "can't write outFile:" + str( err ) )
            raise MobyleError , "Sequence Convertion Error: "+ str( err )
        try:
            squizz_pipe = Popen( cmde ,
                                 shell  = False ,
                                 stdout = outFile ,
                                 stdin  = None ,
                                 stderr = PIPE
                                 )
        except OSError, err:
            msg = "squizz exit abnormally: " + str(err)
            _log.critical( msg )
            raise MobyleError, msg
            
        squizz_pipe.wait()
        err = ''.join( squizz_pipe.stderr.readlines() )
        if squizz_pipe.returncode != 0:
            msg = err
            match = re.search( "Fatal: .*: unsupported format." , err )
            if match:
                _log.error( msg )
                raise  UnSupportedFormatError , msg
            match = re.search( "squizz: invalid option -- n" , err )
            if match:
                msg = "your squizz binary is too old. Please upgrade it"
                _log.critical( msg )
            raise MobyleError , msg
        else:
            outFile.close()
            match = re.search(  "(: \w+)?: (.+) format, (\d+) entries\.$",  err )
            if match:
                detectFormat = match.group(2)
                #seq_nb = int( match.group(3) )
            else:
                raise UnSupportedFormatError , str( err )
            if detectFormat != "UNKNOWN":
                return outFileName 
            else:
                # the inFormat is not recognize  
                raise UnSupportedFormatError 
    
    
    def convertedFormat(self):
        """
        @return: the list of allowed conversion ( inputFormat , outputFormat ) 
        @rtype: [ ( string inputFormat, string outputFormat )  , ... ]
        """
        formats = self.detectedFormat()
        return [ ( inputFormat , outputFomat) for inputFormat in formats for outputFomat in formats ]
    


