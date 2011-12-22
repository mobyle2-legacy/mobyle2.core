"""
This module is used as template to build a converter module
"""




class DataConverter( object ):
    
    def __init__(self, path ):
        self.path = path
        self.program_name = """the name of the tool used to perform the detection/convertion format"""
        
    def detect( self, dataFileName ):
        """
        detect the format of the data.
        @param dataFileName: the absolute filename of the data which the format must be detected
        @type dataFileName: string
        @return: the format of this data and the number of entry. 
               if the format cannot be detected, return None
               if the number of entry cannot be detected, return None
        @rtype: ( string format , int number of entry ) 
        """
        raise NotImplementedError("this method must be overriden")
        return None
    
    def detectedFormat(self):
        """
        @return: the list of detectables formats.
        @rtype: list of stings
        """
        raise NotImplementedError("this method must be overriden")
        return []
    
    
    def convert( self, dataFileName , outputFormat , inputFormat = None):
        """
        convert a data in the format outputFormat
        @param dataFileName: the absolute filename of the data to convert
        @type dataFileName: string
        @param outputFormat: the format in which the data must be convert in.
        @type outputFormat: string
        @param inputFormat: the format of the data 
        @type inputFormat: string
        @return: the filename of the converted data.
        @rtype: string
        @raise UnsupportedFormatError: if the outputFormat is not supported, or if the data is in unsupported format.
        """
        raise NotImplementedError("this method must be overriden")
        return dataFileName 
    
    
    def convertedFormat(self):
        """
        @return: the list of allowed conversion ( inputFormat , outputFormat ) 
        @rtype: [ ( string inputFormat, string outputFormat )  , ... ]
        """
        raise NotImplementedError("this method must be overriden")
        return [ ]



