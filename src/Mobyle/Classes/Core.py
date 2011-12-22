########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

"""
Content the basics Mobyle Parameter types 
"""

import os 
import re
from types import BooleanType , StringTypes
from logging import getLogger
c_log = getLogger(__name__)
b_log = getLogger('Mobyle.builder')

import shutil

from Mobyle.Utils import safeFileName
from Mobyle.Classes.DataType import DataType
from Mobyle.Service import MobyleType

from Mobyle.MobyleError import MobyleError , UserValueError , UnDefAttrError , UnSupportedFormatError
from Mobyle.ConfigManager import Config
_cfg = Config()




def safeMask( mask ):
    import string
    for car in mask :
        if car not in string.printable :
            mask = mask.replace( car , '_')
    #don't use re.UNICODE because safeFileName don't permit to use unicode char.
    #we must work whit the same char set    
    mask = re.sub( "(;|`|$\(\s)+" , '_' , mask )
    mask = re.sub( "^.*[\\\:/]", "" ,  mask  )
    return mask



class DataTypeTemplate( DataType ):

    def convert( self , value , AcceptedMobyleType , detectedMobyleType = None , paramFile= False ):
        """
        cast the value to the right typeand compute the dataFormat conversion if needed (based on the 
        detectedMobyleType and the AcceptedMobyleType)
        @param value: the value provided by the User for this parameter
        @type value: String
        @param acceptedMobyleType: the MobyleType with the Dataformat accepted by this service parameter 
        @type acceptedMobyleType: L{MobyleType} instance
        @param detectedMobyleType: the MobyleType discribing the real dataformat of this data
        @type detectedMobyleType: L{MobyleType} instance
        @return: the casted value and the mobyleType describing this data (with the effective DataFormat)
                 for datatype which have not dataFormat (boolean , integer, ... )
                 the MobyleType returned is the same as the AcceptedMobyleType.
        @rtype: ( value any type , MobyleType instance )
        @raise UseValueError: if the cast failed
        """
        realMobyleType = MobyleType( self )
        return ( "DataTypeTemplate convert: " + str( value ) , realMobyleType )
 
    def detect( self , value ):
        mt = MobyleType( self )
        return mt    
 
    def validate( self, param ):
        """
        do type controls. if the value in the param pass the controls
        return True, False otherwise. 
        @rtype: boolean  
        """
        return "DataTypeTemplate validate"
        
        
        
class BooleanDataType( DataType ):
    """
    """
    def convert( self , value , acceptedMobyleType , detectedMobyleType = None , paramFile= False ):
        """
        cast the value to a Boolean.
        The values: "off", "false", "0" or '' (case insensitive) are false,
        all others values are True.  
        @param value: the value provided by the User for this parameter
        @type value: String
        @param acceptedMobyleType: the MobyleType  accepted by this service parameter 
        @type acceptedMobyleType: L{MobyleType} instance
        @param detectedMobyleType: the MobyleType discribing this data
        @type detectedMobyleType: L{MobyleType} instance
        @return: the value converted to Boolean, and a MobyleType discribing this value
        @rtype: tuple ( boolean , MobyleType instance )
        """
        if value is None:
            # in html form boolean appear as checkbox
            # if the checkbox is not selected
            # the parameter is not send in the request
            return ( False , acceptedMobyleType )
        if isinstance( value , BooleanType ):
            return ( value , acceptedMobyleType )
        elif isinstance( value , StringTypes ):
            value = value.lower()
            if value in [ "off", "false", "0", "", "''", '""' ]:
                return ( False , acceptedMobyleType )
            elif value in [ "on", "true", "1" ]:
                return ( True , acceptedMobyleType )
        else:
            msg = "Invalid value: " + str( value ) + " is not a boolean."
            raise UserValueError( msg = msg )

    def detect( self , value ):
        mt = MobyleType( self )
        return mt
    
    def validate( self, param ):
        """
        do type controls. if the value is True or False or None return True,
        otherwise return False..        
        """
        value = param.getValue()
        if value == True or value == False:
            return True
        else:
            return False


        
class IntegerDataType( DataType ):


    def convert( self , value , acceptedMobyleType , detectedMobyleType = None , paramFile= False ):
        """
        Try to cast the value to Integer. the allowed values are digits
        and strings.
        
        @param value: the value provided by the User for this parameter
        @type value: string
        @param acceptedMobyleType: the MobyleType  accepted by this service parameter 
        @type acceptedMobyleType: L{MobyleType} instance
        @param detectedMobyleType: the MobyleType discribing this data
        @type detectedMobyleType: L{MobyleType} instance
        @return: the value converted to Integer and the mobyleType discribing this value.
        @rtype: ( int , MobyleType instance )
        @raise UserValueError: if the cast fails.
        Unlike python, this method convert "8.0" to 8 and
        raise a UserValueError if you try to convert 8.2 .
        """
        if value is None:
            return ( None , acceptedMobyleType )
        #type controls
            # int("8.0") failed and a  ValueError is raised
            # int(8.1) return 8
        try:
            f= float( value )
            i = int( f )
            if ( (f - i) == 0):
                return ( i , acceptedMobyleType )
            else:
                msg = "\"%s\" : this parameter must be an integer" %value
                raise  UserValueError( msg = msg)
        except OverflowError:
            raise UserValueError( msg = "this value is too big" )
        except ( ValueError , TypeError ):
            msg = "\"%s\" : this parameter must be an integer" %value
            raise UserValueError( msg = msg)

    def detect( self , value ):
        mt = MobyleType( self )
        return mt  
         
    def validate( self, param  ):
        """
        @return True if the value is an integer, False othewise.
        """   
        value = param.getValue()

        if value is None:
            return True                       
        try:
            int( value )
        except ( TypeError , ValueError ):
            return False

class FloatDataType( DataType ):


    def convert( self , value , acceptedMobyleType , detectedMobyleType = None , paramFile= False ):
        """
        Try to cast the value to Float.
        @param value: the value provided by the User for this parameter
        @type value: 
        @param acceptedMobyleType: the MobyleType  accepted by this service parameter 
        @type acceptedMobyleType: L{MobyleType} instance
        @param detectedMobyleType: the MobyleType discribing this data
        @type detectedMobyleType: L{MobyleType} instance
        @return: the value converted to Float
        @rtype: float
        """
        if value is None:
            return ( None , acceptedMobyleType )
        try:
            return ( float( value ) , acceptedMobyleType )
        except ( ValueError, TypeError ):
            msg = str( value ) + " this parameter must be a Float"
            raise UserValueError( msg = msg )

    def detect( self , value ):
        mt = MobyleType( self )
        return mt
    
    def validate( self, param ):
        """
        @return: True if the value is a float, False othewise.
        @rtype: boolean
        """
        value = param.getValue()
        if value is None:
            return True     
        try:
            float( value )
        except ( ValueError , TypeError ):
            return False


class StringDataType( DataType ):

    def convert( self , value , acceptedMobyleType , detectedMobyleType = None , paramFile= False ):
        """
        Try to cast the value to String. 
        
        @param value: the value provided by the User for this parameter
        @type value: 
        @return: the value converted to String.
        @rtype: String
        @param acceptedMobyleType: the MobyleType  accepted by this service parameter 
        @type acceptedMobyleType: L{MobyleType} instance
        @param detectedMobyleType: the MobyleType discribing this data
        @type detectedMobyleType: L{MobyleType} instance
        @raise UserValueError: if the cast fails.
        """
        if value is None:
            return ( None , acceptedMobyleType )
        #type controls
        try:
            value = str( value ).encode('ascii')
        except ValueError :
            raise UserValueError( msg = "should be an (ascii) string" ) 
        #strings with space are allowed, but if the string will appear
        #as shell instruction it must be quoted
        if value.find(' ') != -1 and not paramFile:
            value = "'%s'" % value
        return ( value , acceptedMobyleType )                        
        
    def detect( self , value ):
        mt = MobyleType( self )
        return mt        
    
    def validate( self, param  ):
        """
        @return: True if the value is a string and doesnot contain dangerous characters.
        ( allowed characters: the words , space, ' , - , + , and dot if is not followed by another dot
        and eventually surrounded by commas)
        @rtype: boolean
        @raise UserValueError: if the value does not statisfy security regexp.
        """
        value = param.getValue()
        if value is None:
            return True
        
        #allowed characters:
        #the words , space, ' , - , + , and dot if is not followed by another dot 
        #and eventually surrounded by commas
        reg = "(\w|\ |-|\+|,|@|\.(?!\.))+"
        if re.search( "^(%s|'%s')$" % (reg, reg) ,  value ) :         
            return True
        else:
            msg = "this value: \"" + str( value ) + "\" , is not allowed"
            raise UserValueError( parameter = param , msg = msg )
        

class ChoiceDataType( StringDataType ):
    #the values of ChoiceDataType are literals thus they are String

    def convert( self , value , acceptedMobyleType , detectedMobyleType = None , paramFile= False ):
        """
        The values of ChoiceDataType are literals thus this method try to cast
        the value to string.
        @param value: the value provided by the User for this parameter
        @type value:
        @param acceptedMobyleType: the MobyleType  accepted by this service parameter 
        @type acceptedMobyleType: L{MobyleType} instance
        @param detectedMobyleType: the MobyleType discribing this data
        @type detectedMobyleType: L{MobyleType} instance 
        @return: the value converted in String
        @rtype: string
        """
        if value is None:
            return ( None , acceptedMobyleType )
        try:
            value  = str( value )
            if hasattr( acceptedMobyleType , '_undefValue' ) and value == acceptedMobyleType._undefValue :
                return ( None , acceptedMobyleType )
            else:
                return ( value, acceptedMobyleType )
        except ValueError:
            msg = " this parameter is a Choice its value should be a String" 
            raise UserValueError( msg = msg )
   
    def detect( self , value ):
        mt = MobyleType( self )
        return mt

    def validate( self, param ):
        """
        @return: True if the value is valid. that's mean the value
        should be a string among the list defined in the xml.
        otherwise a MobyleError is raised.
        @rtype: boolean
        @param value: a value from a Choice parameter
        @type value: Choice value
        @raise UserValueError: if the value is not a string or is not among the
        list defined in the xml vlist.
        """
        paramName = param.getName()
        value = param.getValue()
        if param.hasVlist() :
            authorizedValues = param.getVlistValues()
        elif param.hasFlist() :
            authorizedValues = param.getFlistValues()
        else:
            msg = "%s a Choice must have a flist or vlist" %( paramName )
            c_log.error( msg )
            raise MobyleError , msg     
        if value is None or value in authorizedValues:
            return True
        else:
            logMsg = "Unauthorized value for the parameter : %s : authorized values = %s : provided value = %s" %( paramName , 
                                                                                                                  authorizedValues ,
                                                                                                                  value 
                                                                                                                  )
            c_log.error( logMsg )
            msg = "Unauthorized value for the parameter : %s" %( paramName )
            raise UserValueError( parameter = param , msg = msg )
                
               

class MultipleChoiceDataType( StringDataType ):

        
    def convert( self , value , acceptedMobyleType , detectedMobyleType = None , paramFile= False ):
        """
        The MutipleChoiceDataType value are literals thus this method try to cast
        the value to a list of string.
        @param value: the values provided by the User for this parameter
        @type value: list
        @param acceptedMobyleType: the MobyleType  accepted by this service parameter 
        @type acceptedMobyleType: L{MobyleType} instance
        @param detectedMobyleType: the MobyleType discribing this data
        @type detectedMobyleType: L{MobyleType} instance
        @return: a string based on each selected value and joined by the separator.
        @rtype: String .
        @raise UserValueError: if the value can't be converted to a string.
        """    
        if value is None:
            return ( None , acceptedMobyleType )
        try:
            values = [ str( elem ) for elem in value ]
        except ValueError:
            msg  = "this parameter is a MultipleChoice its all values must be Strings" %value 
            raise UserValueError( msg = msg )
        return ( values , acceptedMobyleType )
    
    def detect( self , value ):
        mt = MobyleType( self )
        return mt
    
    def validate( self, param ):
        userValues = param.getValue() #it's a string
        sep = param.getSeparator()
        if sep == '':
            userValues = [ i for i in userValues ]
        else:
            userValues = userValues.split( sep )
        authorizedValues =  param.getVlistValues()
        for value in userValues:
            if value not in authorizedValues :
                msg = "the value %s is not allowed (allowed values: %s)" % (
                str( value ) ,
                str( param.getVlistValues() )
                )
                raise UserValueError( parameter = param , msg = msg )
        return True


class AbstractTextDataType( DataType ):

    def isFile( self ):
        return True  
    
    def head( self , data ):
        return data[ 0 : 50 ]
    
    def cleanData( self , data ):
        """
        convert the data in right encoding and replace windows end of line by unix one.
        """
        # trying to guess the encoding, before converting the data to ascii
        try:
            # trying ascii
            data = unicode(data.decode('ascii','strict'))
        except:
            try:
                # utf8 codec with BOM support
                data = unicode(data,'utf_8_sig')
            except:
                try:
                    # utf16 (default Windows Unicode encoding)
                    data = unicode(data,'utf_16')
                except:
                    # latin1
                    data = unicode(data,'latin1')
        # converting the unicode data to ascii
        data = data.encode('ascii','replace')
        return  re.sub( "\r\n|\r|\n" , '\n' , data )


    def toFile( self , data  , dest , destFileName , src , srcFileName ):
        """
        Write file (of user data) in dest directory .
        @param fileName:
        @type fileName: string
        @param data: the content of the file
        @type data: string
        @param dest: the object in which the data will be copied
        @type dest: Job, Session object
        @param src: the object where the data can be found
        @type src: Job, Session object
        @param srcFileName: the file namae of the data in the src ( basename )
        @type srcFileName: string
        @return: the name of the created file (the basename)
        @rtype: string
        @raise: L{UserValueError} when filename is not allowed (for security reason)
        @raise: L{MobyleError} if an error occured during the file creation
        """
        try:
            destSafeFileName = safeFileName( destFileName )            
        except UserValueError, err:
            raise UserValueError( msg = "this value : %s is not allowed for a file name, please change it" % destFileName )
        abs_DestFileName= os.path.join( dest.getDir() , destSafeFileName )
        # if the user upload 2 files with the same basename safeFileName
        # return the same safeFileName
        # add an extension to avoid _toFile erase the existing file.
        ext = 1
        completeName = abs_DestFileName.split( '.' )
        base = completeName[0]
        suffixe = '.'.join( completeName[1:] )
        while os.path.exists( abs_DestFileName ):
            abs_DestFileName = base + '.' + str( ext ) + '.' + suffixe
            ext = ext + 1
        if src:
            if src.isLocal():
                try:
                    srcSafeFileName = safeFileName( srcFileName )
                except UserValueError, err:
                    raise UserValueError( msg = "this value : %s is not allowed for a file name, please change it" % srcFileName )
                #the realpath is because if the abs_SrcFileName is a soft link ( some results are ) the
                # hardlink point to softlink and it causse ane error : no such file 
                abs_SrcFileName = os.path.realpath( os.path.join( src.getDir() , srcSafeFileName ) )
                try:
                    os.link(  abs_SrcFileName , abs_DestFileName )
                except OSError :
                    #if the src and dest are not on the same device
                    #an OSError: [Errno 18] Invalid cross-device link , is raised
                    try:
                        shutil.copy( abs_SrcFileName , abs_DestFileName )
                    except IOError ,err:
                        # I don't know  - neither the service ( if it exists )
                        #               - nor the job or session ID 
                        # I keep the Job or the Session to log this error 
                        msg = "can't copy data from %s to %s : %s" %( abs_SrcFileName ,
                                                                      abs_DestFileName ,
                                                                      err )
                        c_log.error( msg )
                        raise MobyleError , "can't copy data : "+ str(err)
            else: #src is a job , jobState , MobyleJob instance ( Session is always Local )
                data = src.getOutputFile( srcFileName )
                try:
                    f = open( abs_DestFileName , 'w' )
                    f.write( data )
                    f.close()
                except IOError ,err:
                    msg = "unable to write data from %s to %s: %s"%(src , dest , err )
                    c_log.error( msg )
                    raise MobyleError , msg
        else:
            clean_content = self.cleanData( data )
            try:
                fh = open( abs_DestFileName , "w" )
                fh.write( clean_content )
                fh.close()
            except IOError , err:
                msg = "error when creating file : " + abs_DestFileName + str( err )
                raise MobyleError , msg
        size = os.path.getsize( abs_DestFileName )
        return os.path.basename( abs_DestFileName ) , size
    
    
    @classmethod
    def supportedFormat( cls ):
        """
        @return: the list supported by the format detector
        @rtype: list of string
        """
        uniq_formats = []
        for converter in _cfg.dataconverter( cls.__name__[:-8] ):
            for f in converter.detectedFormat():
                if f not in uniq_formats:
                    uniq_formats.append( f )
        return uniq_formats        
    
    @classmethod         
    def supportedConversion( cls ):
        """
        @return: the list of dataFormat conversion available.
        @rtype: list of tuple [ (string input format, string output formt) , ... ]
        """
        uniq_conversion = []
        for converter in _cfg.dataconverter( cls.__name__[:-8] ):
            for f in converter.convertedFormat():
                if f not in uniq_conversion:
                    uniq_conversion.append( f )
        return uniq_conversion
    
    
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
        if value is None:
            return None
        if len( value ) == 2 :
            src , srcFileName = value
        else:
            raise MobyleError ,"value must be a tuple of 2 elements: ( Job/MobyleJob/JobState or Session instance , Job/MobyleJob/JobState or Session instance , srcFileName )"
        if src and not srcFileName :
            raise MobyleError , "if src is specified, srcFileName must be also specified"
        absFileName = os.path.join( src.getDir() , srcFileName )
        
        all_converters = _cfg.dataconverter( self.__class__.__name__[:-8] )
        for converter in all_converters:
            detected_format , seq_nb = converter.detect( absFileName )
            prg = converter.program_name
            if detected_format:
                detected_mt = MobyleType( self , dataFormat = detected_format , format_program = prg , item_nb = seq_nb) 
                return detected_mt 
        return MobyleType( self ) #no dataFormat have been detected
    
    
    def convert( self , value ,acceptedMobyleType , detectedMobyleType = None,  paramFile= False):
        """
        convert the sequence contain in the file fileName in the rigth format
        throws an UnsupportedFormatError if the output format is not supported
        or a MobyleError if something goes wrong during the conversion.

        @param value: is a tuple ( src , srcFileName) 
          - srcfilename is the name of the file to convert in the src
          - src must be a L{Job} instance the conversion are perform only by jobs (not session) .
        @type value: ( L{Job} instance dest, L{Job} instance, src)
        @return: the fileName ( basename ) of the  sequence file and the effective MobyleType associated to this 
        value
        @rtype: ( string fileName , MobyleType instance )
        @raise UnSupportedFormatError: if the data cannot be converted in any suitable format
        """
        if value is None:
            return None
        if len( value ) == 2 :
            src , srcFileName = value
        else:
            raise MobyleError ,"value must be a tuple of 2 elements: ( Job/MobyleJob/JobState or Session instance , Job/MobyleJob/JobState or Session instance , srcFileName )"
        if src and not srcFileName :
            raise MobyleError , "if src is specified, srcFileName must be also specified"
        absFileName = os.path.join( src.getDir() , srcFileName )
        all_converters = _cfg.dataconverter( self.__class__.__name__[:-8] )
        in_format = detectedMobyleType.getDataFormat()
        
        if not all_converters:
            fileName = safeFileName( absFileName )
            if detectedMobyleType :
                mt = detectedMobyleType
            else:
                mt = MobyleType( self )
            #filename is a basename
            return ( fileName , mt )
        else:
            def unknow_converter( in_format , converters ):
                result = None 
                for converter in converters:
                    try:
                        result = fixed_converter( in_format , converter )
                    except UnSupportedFormatError:
                        continue
                    if result is not None:
                        break
                #if I cannot find any suitable converter result is None    
                return result
                
            def fixed_converter( in_format ,  converter ):
                allowed_conversions = detector_used.convertedFormat()
                for out_format , force in acceptedMobyleType.getAcceptedFormats():
                    if ( in_format , out_format ) in allowed_conversions:
                        try:
                            outFileName = converter.convert( absFileName , out_format , inputFormat = in_format )
                            outFileName = os.path.basename( outFileName )
                        except UnSupportedFormatError, err:
                            raise UserValueError( msg = "a problem occurred during the data conversion : "+str( err ) ) 
                        converted_mt = MobyleType( self  , dataFormat = out_format , format_program = detector_used.program_name )
                        return ( outFileName , converted_mt )
                #it's not a suitable converter
                return None
            
            if detectedMobyleType.format_program is None:
                result = unknow_converter( in_format , all_converters )
            else:
                for converter in all_converters:
                    if converter.program_name == detectedMobyleType.format_program :
                        detector_used = converter
                        break
                if detector_used is None:
                    raise MobyleError( "unable to find %s converter" % detectedMobyleType.format_program )
                result  = fixed_converter( in_format , detector_used )
                if result is None:# the detector_used is not suitable for the conversion
                    result= unknow_converter( in_format , [ c for c in all_converters if c != detector_used ] )
                    
            if result is None:
                raise UnSupportedFormatError( "unable to convert %s in %s sequence format" %( in_format , 
                                                                                              [ f[0] for f in acceptedMobyleType.getAcceptedFormats() ] 
                                                                                               ) )
            else:
                return result #( outFileName , converted_mt )
            
 
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
                    #getFilenames return a list of strings representing a unix file mask which is the result of a code evaluation
                    #getFilenames return None if there is no mask for a parameter.
                    filenames = param.getFilenames( ) 
                    for filename in filenames :
                        if filename is None:
                            continue
                        mask = safeMask( filename )
                        if debug > 1:
                            b_log.debug( "filename= %s    safeMask = %s"%(filename, mask))
                        if  not mask or mask != filename :
                            msg = "The Parameter:%s, have an unsecure filenames value: %s " %( param.getName() ,
                                                                                                filename )
                            c_log.error( admMsg = "MobyleJob._validateParameters : " + msg ,
                                            logMsg = None ,
                                            userMsg = "Mobyle Internal Server Error"
                                            )
                            if debug == 0:
                                c_log.critical( "%s : %s : %s" %( self._service.getName(),
                                                                       self._job.getKey() ,
                                                                       msg          
                                                                       )
                                                                       )
                            raise MobyleError , "Mobyle Internal Server Error" 
                        else:
                            if debug > 1:
                                b_log.debug( "filename = %s ...........OK" % filename )
                except UnDefAttrError :
                    b_log.debug("no filenames")
        else:
            if value is None:
                #un infile Text ne peut pas avoir de vdef mais peut il etre a None?
                #=> oui s'il n'est pas obligatoire
                return True
            else:
                return os.path.exists( param.getValue() )
        


class TextDataType( AbstractTextDataType ):
    # this trick is to avoid that SequenceDataType is a subclass of TextDataType
    pass


class ReportDataType( AbstractTextDataType ):
    pass


class BinaryDataType( DataType ):

    def isFile( self ):
        return True
    
    def head( self , data ):
        return 'Binary data'
            
    def cleanData( self, data ):
        """
        prepare data prior to write it on a disk
        @param data: 
        @type data:a buffer
        """
        return data


    def toFile( self , data , dest , destFileName , src , srcFileName ):
        """
        Write file (of user data) in the working directory .
        @param fileName:
        @type fileName: string
        @param content: the content of the file
        @type content: string
        @return: the name ( absolute path ) of the created file ( could be different from the arg fileName )
        @rtype: string
        @call: L{MobyleJob._fillEvaluator}
        """
        try:
            destSafeFileName = safeFileName( destFileName )
        except UserValueError, err:
            raise UserValueError( msg = "this value : %s is not allowed for a file name, please change it" % destFileName )
        abs_DestFileName = os.path.join( dest.getDir() , destSafeFileName )

        # if the user upload 2 files with the same basename safeFileName
        # return the same safeFileName
        # add an extension to avoid _toFile to erase the existing file.
        ext = 1
        completeName = abs_DestFileName.split( '.' )
        base = completeName[0]
        suffixe = '.'.join( completeName[1:] )
        while os.path.exists( abs_DestFileName ):
            abs_DestFileName = base + '.' + str( ext ) + '.' + suffixe
            ext = ext + 1
        if src:
            if src.isLocal():
                try:
                    srcSafeFileName = safeFileName( srcFileName )
                except UserValueError, err:
                    raise UserValueError( msg = "this value : %s is not allowed for a file name, please change it" % srcFileName  )
                
                #the realpath is because if the abs_SrcFileName is a soft link ( some results are ) the
                #hardlink point to softlink and it cause an error : no such file  
                abs_SrcFileName = os.path.realpath( os.path.join( src.getDir() , srcSafeFileName ) )
                try:
                    os.link(  abs_SrcFileName , abs_DestFileName )
                except OSError :
                    #if the src and dest are not on the same device
                    #an OSError: [Errno 18] Invalid cross-device link , is raised
                    try:
                        shutil.copy( abs_SrcFileName , abs_DestFileName )
                    except IOError ,err:
                        # je ne connais - ni le service (s'il existe)
                        #               - ni le l' ID du job ou de la session
                        # donc je laisse le soin au Job ou la session a logger l'erreur
    
                        msg = "can't copy data from %s to %s : %s" %( abs_SrcFileName ,
                                                                      abs_DestFileName ,
                                                                      err )
                        raise MobyleError , "can't copy data : "+ str(err)
            else: #src is a job , jobState , MobyleJOb instance ( session is Local )
                data = src.getOutputFile( srcFileName )
                try:
                    f = open( abs_DestFileName , 'wb' )
                    f.write( data )
                    f.close()
                except IOError ,err:
                    pass
        else:
            try:
                fh = open( abs_DestFileName , "wb" )
                fh.write( data )
                fh.close()
            except IOError , err:
                # je ne connais - ni le service (s'il existe)
                #               - ni le l' ID du job ou de la session
                # donc je laisse le soin au Job ou la session a logger l'erreur
                msg = "error when creating file %s: %s" %( os.path.basename( abs_DestFileName ) ,  err )
                raise MobyleError , msg
        size  = os.path.getsize( abs_DestFileName )
        return os.path.basename( abs_DestFileName ) , size
    
    def detect( self , value ):
        mt = MobyleType( self )
        return mt
    
    def convert( self , value , acceptedMobyleType , detectedMobyleType = None , paramFile= False ):
        """
        Do the generals control and cast the value in the right type.
        if a control or the casting fail a MobyleError is raised

        @param value: the value provided by the User for this parameter
        @type value: String
        @param acceptedMobyleType: the MobyleType  accepted by this service parameter 
        @type acceptedMobyleType: L{MobyleType} instance
        @param detectedMobyleType: the MobyleType discribing this data
        @type detectedMobyleType: L{MobyleType} instance
        @return: the fileName ( basename ) of the binary file
        """
        if value is None:
            return None
        elif len( value ) == 5 :
            data , dest , destFileName , src , srcFileName = value
        else:
            raise MobyleError ,"value must be a tuple of 5 elements: ( data , dest , destFileName , src , srcFileName )"
        if destFileName is None:
            return None
        if dest is None:
            raise MobyleError, "the destination is mandatory"
        if  data and src :
            raise MobyleError, "you cannot specify data and src at the same time"
        if not data and ( not dest or not src ) :
            raise MobyleError , "if data is not specified, dest and src must be defined"
        if src and not srcFileName :
            raise MobyleError , "if src is specified, srcFileName must be also specified"
        #safeFileName return a basename
        fileName = safeFileName( destFileName )
        mt = MobyleType( self )
        return ( fileName , mt )


    def validate( self, param ):
        """
        @todo: il faudrait avoir value = None et verifier file names
        """
        if param.isout():
            value = param.getValue()
            if value is None :
                return True
            else:
                return False
        else:        
            return os.path.exists( param.getValue() )
        


class FilenameDataType( DataType ):
 
    def convert( self , value , acceptedMobyleType , detectedMobyleType = None , paramFile= False ):  
        """
        @param acceptedMobyleType: the MobyleType  accepted by this service parameter 
        @type acceptedMobyleType: L{MobyleType} instance
        @param detectedMobyleType: the MobyleType discribing this data
        @type detectedMobyleType: L{MobyleType} instance
        """  
        if value is None:
            return ( None , acceptedMobyleType )
            #raise UserValueError( parameter = param , msg= " this parameter must be a String" )
        fileName = safeFileName( value )
        return ( fileName , acceptedMobyleType )
    
    def detect( self , value ):
        mt = MobyleType( self )
        return mt    
    
    def validate( self, param ):
        value = param.getValue()
        if value is None :
            return True
        safefileName = safeFileName( value )
        if safefileName != value:
            msg = "invalid value: %s : the followings characters \:/ ;` {} are not allowed" %( value )
            raise UserValueError( parameter = param , msg = msg )
        else:
            return True


    
        

