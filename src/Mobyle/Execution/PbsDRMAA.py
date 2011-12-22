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


class PbsDRMAA(DRMAA):
    """
    Run the commandline by a system call
    """
    def __init__( self, drmaa_config ):
        super( PbsDRMAA , self ).__init__( drmaa_config )
        # workaround the bug in librmaa from opendsp
        if 'HOME' not in os.environ:
                os.environ[ 'HOME' ] = '/dev/null'
