########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

import os 
from hashlib import md5

from Mobyle.AnonymousSession import AnonymousSession
from Mobyle.AuthenticatedSession import AuthenticatedSession
from Mobyle.MobyleError import SessionError , AuthenticationError 
from logging import getLogger

class SessionFactory( object ):
    """
    This class defines a session, that stores all the information
    about a user that should be persistent on the server
    @organization: Institut Pasteur
    @contact:mobyle@pasteur.fr
    """
    __ref = None


    def __new__( cls , cfg ):
        if cls.__ref is  None:
            self = super( SessionFactory , cls ).__new__( cls )
            self.log = getLogger( 'Mobyle.Session.SessionFactory' )
            self.cfg = cfg
            self.__sessions = {}
            cls.__ref = self

        return cls.__ref

    #OPENID, call by openid , do not check password
    def getOpenIdAuthenticatedSession( self , userEmailAddr , ticket_id=None ):
        """
        @return: an already existing openid authenticated session.
        @param userEmailAddr: the user email
        @type userEmailAddr: a Mobyle.Net.EmailAddress instance
        @raise AuthenticationError: the session doesn't already exists
        """
        mymd5 = md5()
        mymd5.update( str( userEmailAddr ) )
        key = mymd5.hexdigest()
        try:
            session = self.__sessions[ key ]
            return session
        except KeyError:
            sessionDir = os.path.normpath( os.path.join( self.cfg.user_sessions_path() , AuthenticatedSession.DIRNAME , key  ) )

            if os.path.exists( sessionDir ):
                session = AuthenticatedSession( self.cfg , userEmailAddr , passwd=None, ticket_id=ticket_id )
                self.__sessions[ session.getKey() ] = session
                return session
            else:
                raise AuthenticationError , "There is no user with this email"



    def getAuthenticatedSession( self , userEmailAddr , passwd=None, ticket_id=None ):
        """
        @return: an already existing authenticated session.
        @param userEmailAddr: the user email
        @type userEmailAddr: a Mobyle.Net.EmailAddress instance
        @param passwd: the session pass word 
        @type passwd: string
        @raise AuthenticationError: if the passwd doesn't match the session passwd
        @raise AuthenticationError: the session doesn't already exists
        """
        mymd5 = md5()
        mymd5.update( str( userEmailAddr ) )
        key = mymd5.hexdigest()

        try:
            session = self.__sessions[ key ]
            if session.checkPasswd( passwd ):
                return session
            else:
                raise AuthenticationError , "There is no user with this email and password"
       
        except KeyError: 
            sessionDir = os.path.normpath( os.path.join( self.cfg.user_sessions_path() , AuthenticatedSession.DIRNAME , key ) )
          
            if os.path.exists( sessionDir ):
                session = AuthenticatedSession( self.cfg , userEmailAddr , passwd=passwd, ticket_id=ticket_id )
                self.__sessions[ session.getKey() ] = session  
                return session
            else: 
                raise AuthenticationError , "There is no user with this email" 



    def getAnonymousSession( self , key = None ):
        """
        @return: an anonymous session. If key is None create a new anonymous session
        @rtype: Session object
        @param key: the key to identify a anonymous session
        @type key: string
        @raise SessionError: if key is specified and doesn't match any session.
        """
        anonymousSessionAllowed = self.cfg.anonymousSession()
        if anonymousSessionAllowed== 'no':
            self.log.error("SessionFactory/can't create anonymous session ANONYMOUS_SESSION is set to \"no\" in Local/Config/Config.py")          
            raise SessionError , "can't create anonymous session: permission denied"
        try:
            session = self.__sessions[ key ]
        except KeyError: 
            if key :
                sessionDir = self.__getSessionDir( key )
                
                if os.path.exists( sessionDir ):
                    self.log.debug( "SessionFactory.getAnonymousSession( key= %s )/ the dir exist I 'll return this session" % key)
                    session = AnonymousSession( self.cfg , key )
                else: 
                    self.log.error( "can't retrieve anonymous session, the Key: %s doesn't match with any Session" % key )
                    raise SessionError , "wrong Key: %s" % key
                   
            else: #new session
                session = AnonymousSession( self.cfg )
                self.log.debug( "SessionFactory.getAnonymousSession( key= %s ) / a new anonymous has been created . I 'll return this session" % key)
                
            self.__sessions[session.getKey()] = session  
            
        self.log.debug( "SessionFactory.getAnonymousSession( key= %s ) I return this anonymous session :key=" + str( session.getKey() )) 
        return session
   

    def createAuthenticatedSession( self , userEmailAddr , passwd ):
        """
        create an authenticated session with email as login and passwd as pass word
        @param userEmailAddr: the user email
        @type userEmailAddr: a Mobyle.Net.EmailAddress object
        @param passwd: the user password
        @type passwd: string
        @return: a new authenticated session
        @rtype: session instance
        @raise AuthenticationError: if there is already a session with this email, or the email is not allowed on this server
        """
        authenticatedSessionAllowed = self.cfg.authenticatedSession()
      
        if authenticatedSessionAllowed == 'no':
            self.log.error("can't create  session AUTHENTICATED_SESSION is set to \"no\" in Local/Config/Config.py")          
            raise SessionError , "can't create  authenticated session: permission denied"

        mymd5 = md5()
        mymd5.update( str( userEmailAddr ) )
        key = mymd5.hexdigest()

        if self.__sessions.has_key( key ) : 
            msg = "Try to create a new Session with email %s, the %s Session already exist" % ( userEmailAddr , key)
            self.log.error( msg )        
            raise AuthenticationError , "user with the email you specify already exist" 
       
        else:  
            sessionDir = os.path.normpath( os.path.join( self.cfg.user_sessions_path() , AuthenticatedSession.DIRNAME , key ) )
          
            if os.path.exists( sessionDir ):
                msg = "Try to create a new Session with email %s, the %s Session already exist" % ( userEmailAddr , key)
                self.log.error( msg )
                raise AuthenticationError , "user with the email you specify already exist" 
                
            session = AuthenticatedSession( self.cfg , userEmailAddr , passwd )
            self.__sessions[ session.getKey() ] = session   
            return session
  

    def removeSession( self , key ):
        sessionDir = self.__getSessionDir(  key )
       
        for File in os.listdir( sessionDir ):
            os.unlink( os.path.join( sessionDir , File ) )
        os.rmdir( sessionDir )
        del self.__sessions[ key ]


    def __getSessionDir( self , key ) :
 
        if  len ( key ) == 32  :
            #a md5 value is always encode in 32 char
            return os.path.normpath( os.path.join( self.cfg.user_sessions_path() , AuthenticatedSession.DIRNAME , key  ) )
        else:
            ##the anonymous key have 15 char length
            return os.path.normpath( os.path.join( self.cfg.user_sessions_path() , AnonymousSession.DIRNAME , key ) )
 
 
    

