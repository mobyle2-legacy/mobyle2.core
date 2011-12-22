########################################################################################
#                                                                                      #
#   Author: Bertrand Neron                                                             #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

import os
import sys
import errno

MOBYLEHOME = os.path.abspath( os.path.join( os.path.dirname( __file__ ) , "../../../" ) )
os.environ['MOBYLEHOME'] = MOBYLEHOME

if ( MOBYLEHOME ) not in sys.path:
    sys.path.append( MOBYLEHOME )
if ( os.path.join( MOBYLEHOME , 'Src' ) ) not in sys.path:    
    sys.path.append( os.path.join( MOBYLEHOME , 'Src' ) )

import Mobyle.Test.MobyleTest

from Mobyle.Transaction import Transaction


def openTransaction( path , type ):
    try:
        transaction = Transaction( path , type )
    except IOError , err:
        if err.errno == errno.EAGAIN:
            # the assertion is made on the return status if it True or False
            # EAGAIN = Resource temporarily unavailable
            sys.exit(errno.EAGAIN)
        else:
            import traceback
            print >> sys.stderr , traceback.print_exc()
            raise err
    transaction.commit()
    
    
if __name__ == '__main__':
    path = sys.argv[1]
    type = int( sys.argv[2])
    openTransaction( path , type)
