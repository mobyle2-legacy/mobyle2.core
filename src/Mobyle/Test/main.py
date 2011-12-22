#! /usr/bin/env python

import os
import sys
import unittest2 as unittest

MOBYLEHOME = os.path.abspath( os.path.join( os.path.dirname( __file__ ) , "../../../" ) )
os.environ[ 'MOBYLEHOME' ] = MOBYLEHOME
if ( MOBYLEHOME ) not in sys.path:
    sys.path.append( MOBYLEHOME )
if ( os.path.join( MOBYLEHOME , 'Src' ) ) not in sys.path:    
    sys.path.append( os.path.join( MOBYLEHOME , 'Src' ) )
    
import Mobyle.Test.MobyleTest        
from optparse import OptionParser    
parser = OptionParser()
parser.add_option("-v", "--verbose" , 
                  dest= "verbosity" , 
                  action="count" , 
                  help= "set the verbosity level of output",
                  default = 0
                  )
opt , args = parser.parse_args()    

if not args:
    suite = unittest.TestLoader().discover( '.' ) 
else:
    suite = unittest.TestSuite()
    for arg in args: 
        if os.path.exists( arg ):
            if os.path.isfile( arg ):
                fpath, fname =  os.path.split( arg )
                suite.addTests( unittest.TestLoader().discover(  fpath , pattern = fname ) ) 
            elif os.path.isdir( arg ):  
                suite.addTests( unittest.TestLoader().discover( arg ) ) 
        else:
            sys.stderr.write(  "%s : no such file or directory\n" % arg ) 

unittest.TextTestRunner( verbosity = opt.verbosity ).run( suite )
