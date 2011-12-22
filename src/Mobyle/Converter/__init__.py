########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.        #
#                                                                                      #
########################################################################################

import glob 
import os 


MOBYLEHOME = None
if os.environ.has_key('MOBYLEHOME'):
    MOBYLEHOME = os.environ['MOBYLEHOME']
if not MOBYLEHOME:
    import sys
    sys.exit('MOBYLEHOME must be defined in your environment')

for f in glob.glob( os.path.join( MOBYLEHOME , 'Src' , 'Mobyle' , 'Converter' , '*.py' ) ):
    module_name = os.path.splitext( os.path.basename(f) )[0]
    if module_name != '__init__':
        try: 
            module = __import__( module_name , globals(), locals(), [ module_name ])
            klass = getattr( module , module_name)
            locals()[ module_name ] = klass
        except Exception , e:
            continue