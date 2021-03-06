########################################################################################
#                                                                                      #
#   Author: Sandrine Larroude                                                          #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

"""
Content the Mobyle Parameter types related to genomic bioloy
"""
 

from logging import getLogger
c_log = getLogger(__name__)
b_log = getLogger('Mobyle.builder')

from Mobyle.MobyleError import MobyleError , UnDefAttrError
from Mobyle.Classes.Core import AbstractTextDataType , safeMask
from Mobyle.ConfigManager import Config
_cfg = Config()



class AlignmentDataType( AbstractTextDataType ):
    
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
        detected_mt = super( AlignmentDataType , self ).detect( value )
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
        @return: True if the value is valid, False otherwise
        """
        value = param.getValue()
        if param.isout():
            if value is not None : #not possible for the user to modify an isout parameter 
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
    
                    #getFilenames returns a list of unix file mask, result of a code evaluation
                    #None is returned if there is no mask for a parameter.
                    masks = param.getFilenames( ) 
                    for mask in masks :
                        if mask is None:
                            continue
                        mySafeMask = safeMask( mask )
                        if debug > 1:
                            b_log.debug( "filename= %s    safeMask = %s" % (mask, mySafeMask))
                        if  not mySafeMask or mySafeMask != mask :
                            raise MobyleError , "have an unsecure filenames value before safeMask: %s , after safeMask: %s" % (mask, mySafeMask)
                        elif debug > 1:
                            b_log.debug( "filename = %s ...........OK" % mask )
                                               
                except UnDefAttrError :
                    b_log.debug("no filenames")

        else:
            if value is None:
                return True
            else:
                return True            
             