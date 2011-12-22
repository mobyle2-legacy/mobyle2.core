########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

import os 
import logging
_log = logging.getLogger(__name__)

from Mobyle.Execution.DRMAA import DRMAA


class LsfDRMAA(DRMAA):
    def __init__( self, drmaa_config ):
        os.environ[ 'LSF_ENVDIR']    = drmaa_config.envdir
        os.environ[ 'LSF_SERVERDIR'] = drmaa_config.serverdir
        super( LsfDRMAA , self ).__init__( drmaa_config )
        self.nativeSpecification = '' 
        #I set a more permissive umask
        #to allow LSF to generate some internal scripts
        #( see JOB_SPOOL_DIR ) with x permissions 
        os.umask(0012)