########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

from Mobyle.MobyleError import MobyleError


class Status:

    _CODE_2_STATUS = { 
                     -1 : "unknown"   , # the status cannot be determined
                      0 : "building"  , # the job directory has been created
                      1 : "submitted" , # the job.run method has been called
                      2 : "pending"   , # the job has been submitted to the batch manager but wait for a slot 
                      3 : "running"   , # the job is running in the batch manager
                      4 : "finished"  , # the job is finished without error from Mobyle
                      5 : "error"     , # the job has failed due to a MobyleError 
                      6 : "killed"    , # the job has been removed by the user, or killed by the admin
                      7 : "hold"      , # the job is hold by the batch manager
                      }
    
    def __init__(self , code = None , string = None , message = ''):
        """
        @param code: the code of the status 
        @type code: integer 
        @param string: the code of the status representing by a string
        @type string: string
        @param message: the message associated to the status
        @type message: string
        """
        if code is None and not string :
            raise MobyleError , "status code or string must be specified"
        elif code is not None and string :
            raise MobyleError, "status code or string must be specified, NOT both"
        elif code is not None :
            if code in self._CODE_2_STATUS.keys():
                self.code = code
            else:
                raise MobyleError , "invalid status code : " + str( code )
        elif string:
            if string in  self._CODE_2_STATUS.values():
                iterator = self._CODE_2_STATUS.iteritems()
                for code , status in iterator:
                    if status == string:
                        self.code = code
            else:
                raise MobyleError , "invalid status : " + str( string ) 
        
        if message:
            self.message = message
        else:
            self.message = ''
            
        
    def __eq__(self , other):
        return self.code == other.code and self.message == other.message
    
    def __ne__(self , other ):
        return self.code != other.code or self.message != other.message
    
    def __str__(self):
        return self._CODE_2_STATUS[ self.code ]
    
    def isEnded(self):
        """
         4 : "finished"  , # the job is finished without error from Mobyle
         5 : "error"     , # the job has failed due to a MobyleError 
         6 : "killed"    , # the job has been removed by the user, or killed by the admin
        """
        return self.code in ( 4 , 5 , 6 )

    def isOnError(self):
        """
         5 : "error"     , # the job has failed due to a MobyleError 
         6 : "killed"    , # the job has been removed by the user, or killed by the admin
        """
        return self.code in ( 5 , 6 )
        
    def isQueryable(self):
        """
        1 : "submitted" , # the job.run method has been called
        2 : "pending"   , # the job has been submitted to the batch manager but wait for a slot 
        3 : "running"   , # the job is running in the batch manager
        7 : "hold"      , # the job is hold by the batch manager
        """
        return self.code in( 1 , 2 , 3 , 7 )
    
    def isKnown(self):
        return self.code != -1
