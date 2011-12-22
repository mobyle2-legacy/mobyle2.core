########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

import os 
import sys
import random 
import string
from time import time

from Mobyle.Session import Session
from Mobyle.Transaction import Transaction
from Mobyle.MobyleError import MobyleError , SessionError 
from logging import getLogger



class AnonymousSession( Session ):

    DIRNAME = 'anonymous'
 
    def __init__( self ,  cfg  , key = None):
        self.cfg = cfg
        self.log = getLogger('Mobyle.Session.AnonymousSession')
        """the maximum size of a session ( in bytes )"""
        self.sessionLimit = self.cfg.sessionlimit()
        anonymousSessionAllowed = self.cfg.anonymousSession()
        self._modifiedTransaction = False
       
        if anonymousSessionAllowed == 'no':
            self.log.error("can't create anonymous session ANONYMOUS_SESSION is set to \"no\" in Local/Config/Config.py")          
            raise MobyleError , "can't create anonymous session: permission denied"

        if key :
            self.Dir = os.path.normpath( os.path.join( self.cfg.user_sessions_path() , AnonymousSession.DIRNAME , key ) )
            if not os.path.exists( self.Dir ):
                self.log.error( "can't retrieve anonymous session, the Key: %s doesn't match with any Session" % key )
                raise SessionError , "wrong key : %s" % key

            self.key = key
            self.log.debug( "%f : %s return new annonymousSession based on old dir call by= %s" %( time() ,
                                                                                                self.getKey()  , 
                                                                                                os.path.basename( sys.argv[0] ) ,
                                                                                                ))
              
        else: #create a new session
            self.key = self.__newSessionKey( )
            """ the user/session  key"""
            self.Dir = os.path.normpath( os.path.join( self.cfg.user_sessions_path() , AnonymousSession.DIRNAME , self.key ) )
            """ the path to this session directory """
           
            if os.path.exists( self.Dir ):
                msg = "Try to make a new anonymous session with key: %s. This directory already exist" % self.key
                self.log.critical( msg )
                raise SessionError , "can't create new anonymous session"
            try:
                os.makedirs( self.Dir , 0755 ) #create parent directory
            except Exception, err:
                self.log.critical( "unable to create anonymous session : %s : %s" %( self.Dir , err) , exc_info = True)
                raise SessionError , "unable to create anonymous session"
            
            if anonymousSessionAllowed == 'yes':
                Transaction.create( os.path.join( self.Dir, self.FILENAME ) , False , True )
            else:#anonymousSessionAllowed == 'captcha'
                Transaction.create( os.path.join( self.Dir , self.FILENAME ) , False , False )
           
            self.log.debug( "%f : %s  create a new session call by= %s" %( time() ,
                                                                        self.getKey()  , 
                                                                        os.path.basename( sys.argv[0] ) ,
                                                                        ))
        self.url = "%s/%s/%s" % (self.cfg.user_sessions_url(), AnonymousSession.DIRNAME, self.key)

    def isAuthenticated( self ):
        return False
   
    
    
    def getCaptchaProblem( self ):
        """
        @return: a png image which is a captcha
        @rtype:
        """
        from Mobyle.Captcha import Captcha 
        import StringIO
        captcha = Captcha.PseudoGimpy()
       
        transaction = self._getTransaction( Transaction.WRITE )
        transaction.setCaptchaSolution( captcha.solutions[0] )
        transaction.commit()
        pf = StringIO.StringIO()
        captcha.render().save( pf , "PNG" )
       
        return pf.getvalue()
  
             
    def checkCaptchaSolution( self , solution ):
        """
        check if solution is the solution to the current problem
        @param solution: the solution to the current problem
        @type solution: string
        @return: True if solution is the solution of the current captcha problem, False otherwise
        @rtype: boolean
        """
        transaction = self._getTransaction( Transaction.READ )
        current_captcha_sol = transaction.getCaptchaSolution()
        transaction.commit()
        
        if current_captcha_sol is None :
            msg = "session key: %s : you must getCaptchaProblem before ask for CaptchaSolution" % self.getKey()
            self.log.error( msg )
            raise SessionError , msg
       
        if solution == current_captcha_sol :
            transaction = self._getTransaction( Transaction.WRITE )
            transaction.activate()
            transaction.commit()
            return True
        else:
            return False
     
     
    def __newSessionKey( self ):
        """
        @return: a unique id for the session
        @rtype: string
        """
        letter = string.ascii_uppercase[ random.randrange( 0 , 26 ) ]
        strTime = "%.9f" % time()
        strTime = strTime[-9:]
        strPid = "%05d" % os.getpid()
        strPid = strPid.replace( '.' , '' )[ -5 : ]
        return letter + strPid + strTime

