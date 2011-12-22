########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

"""
Content the Mobyle Parameter types related to the genomic bioloy
"""
 

from logging import getLogger
c_log = getLogger(__name__)
b_log = getLogger('Mobyle.builder')

from Mobyle.MobyleError import MobyleError , UnDefAttrError 
from Mobyle.Classes.Core import AbstractTextDataType , safeMask
from Mobyle.ConfigManager import Config
_cfg = Config()


class SequenceDataType( AbstractTextDataType ):
    
    def detect( self , value  ):
        """
        detects the format of the sequence(s) contained in fileName
        @param value: the src object and the filename in the src of the data to detect
        @type value: tuple ( session/Job/MobyleJob instance , string filename )
        @return: a tuple of the detection run information:
            - the detected format,
            - the detected items number,
            - program name used for the detection.
        """
        detected_mt = super( SequenceDataType , self ).detect( value )
        squizzDir = _cfg.format_detector_cache_path()
        if squizzDir :
            ##############################################
            # This part of is used to back up all        # 
            # submitted sequences which are not detected # 
            # by squizz for further analysis             #
            ##############################################
            squizz_detector = None
            for detector in _cfg.dataconverter( self.__class__.__name__[:-8] ):
                if detector.program_name == 'squizz':
                    squizz_detector = detector
                    break
            if squizz_detector is not None :
                detected_data_format = detected_mt.getDataFormat()
                from os import link
                from os.path import join as os_join
                if ( detected_data_format is None ) or ( detected_data_format in squizz_detector.detectedFormat() and not detected_mt.getFormatProgram() == 'squizz' ):
                    try:
                        #dump the data to further annalysis 
                        link(  os_join( value[0].getDir() , value[1] ) , 
                               os_join( squizzDir , "%s_%s_%s"%( self.__class__.__name__[:-8] ,
                                                                 value[0].getKey() ,
                                                                 value[1] ) )
                               )
                    except Exception , err : 
                        c_log.error( "unable to link data in  format_detector_cache_path : %s " % err ) 
        return detected_mt
    
 
    def validate( self , param ):
        """
        """
        value = param.getValue()

        if param.isout():
            if value is not None : #un parametre isout ne doit pas etre modifier par l'utilisateur 
                return False
            else:
                #####################################################
                #                                                   #
                #  check if the Parameter have a secure filenames   #
                #                                                   #
                #####################################################
                try:
                    debug = param.getDebug()
                    if debug > 1:
                        b_log.debug( "check if the Parameter have a secure filename" )
    
                    #getFilenames return list of strings representing a unix file mask which is the result of a code evaluation
                    #getFilenames return None if there is no mask for a parameter.
                    filenames = param.getFilenames( ) 
                    for filename in filenames :
                        if filename is None:
                            continue
                        mask = safeMask( filename )
                        if debug > 1:
                            b_log.debug( "filename= %s    safeMask = %s"%(filename, mask))
                        if  not mask or mask != filename :
                            raise MobyleError , "have an unsecure filenames value before safeMask: %s , after safeMask: %s"%( filename , mask )
                        else:
                            if debug > 1:
                                b_log.debug( "filename = %s ...........OK" % filename )
                                               
                except UnDefAttrError :
                    b_log.debug("no filenames")
        else:#the param is an inFile
            if value is None:
                return True
            else:
                return True
