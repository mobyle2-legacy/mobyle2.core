
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


class SgeDRMAA(DRMAA):
    def __init__( self, drmaa_config ):
        os.environ[ 'SGE_ROOT'] = drmaa_config.root
        os.environ[ 'SGE_CELL'] = drmaa_config.cell
        super( SgeDRMAA , self ).__init__( drmaa_config )
