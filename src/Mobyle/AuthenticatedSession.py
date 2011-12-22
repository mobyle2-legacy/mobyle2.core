########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

import os
from hashlib import md5
from time import  time , sleep 
import random

from Mobyle.Session import Session
from Mobyle.Transaction import Transaction
from Mobyle.MobyleError import MobyleError , SessionError , AuthenticationError
from Local.Policy import authenticate as policy_authenticate

from logging import getLogger


class AuthenticatedSession( Session ):
    
    VALID    = 1
    REJECT   = 0
    CONTINUE = 2

    DIRNAME  = 'authentified'

    def __init__( self , cfg , userEmail , passwd=None, ticket_id=None):
        self.log = getLogger('Mobyle.Session.AuthenticatedSession')
        self.cfg = cfg
        assert not(passwd and ticket_id), "please provide either a ticket id or a password" # TODO: clean up the parameters check
        """the maximum size of a session ( in bytes )"""
        self.sessionLimit = self.cfg.sessionlimit()
        self.__userEmail = userEmail
        authenticatedSessionAllowed = self.cfg.authenticatedSession()        
        
        if authenticatedSessionAllowed == "no" :
            self.log.error("can't create  session AUTHENTICATED_SESSION is set to \"no\" in Local/Config/Config.py")          
            raise SessionError , "can't create  authenticated session: permission denied"
              
        key = self.__newSessionKey()
        sessionDir = os.path.normpath( os.path.join( self.cfg.user_sessions_path() , AuthenticatedSession.DIRNAME , key  ) )
        self.key = key 
        """ the user/session  key"""
        self.Dir = sessionDir
        """ the path to this session directory """
       
        if os.path.exists( sessionDir ): #the session already exist
            if passwd:
                if not self.checkPasswd( passwd ):
                    self.log.info( "authentified/%s : Authentication Failure "% ( self.getKey() ) )
                    raise AuthenticationError , "Authentication Failure"
                else:
                    self._getTicket()
            elif ticket_id and not self.checkTicket( ticket_id ):
                raise AuthenticationError , "Invalid ticket or expired ticket"
            else:
                self.__generateTicketId(ticket_id or None)
            
        else: #creation of new Session
            chk = self.__userEmail.check()
            if not chk:
                msg = " %s %s FORBIDDEN can't create authenticated session : %s" % ( self.__userEmail ,
                                    os.environ[ 'REMOTE_ADDR' ] ,
                                    self.__userEmail.getMessage()
                                    )
                self.log.error( msg )
                raise SessionError , "you are not allowed to register on this server for now"
            try:
                os.makedirs( sessionDir , 0755 ) #create parent directory 
            except Exception, err:
                self.log.critical( "unable to create authenticated session : %s : %s" % ( sessionDir , err) , exc_info = True)
                raise SessionError , "unable to create authenticated session"
            mymd5 = md5()
            mymd5.update( passwd )
            cryptPasswd = mymd5.hexdigest()
            
            authenticatedSessionAllowed = self.cfg.authenticatedSession()        
            if authenticatedSessionAllowed == "yes":  
                Transaction.create( os.path.join( sessionDir , self.FILENAME ) , 
                                    True , #authenticated
                                    True , #activated
                                    userEmail = str( self.__userEmail ) , 
                                    passwd = cryptPasswd )
                self.__generateTicketId()
            elif authenticatedSessionAllowed == "email" :
                activatingKey = self.__newActivatingKey()
                try:
                    from Mobyle.Net import Email
                    mail = Email( self.__userEmail )
                    mail.send( 'CONFIRM_SESSION' , { 'SENDER'         : self.cfg.sender() ,
                                                     'HELP'           : self.cfg.mailHelp() ,
                                                     'SERVER_NAME'    : self.cfg.portal_url() ,
                                                     'ACTIVATING_KEY' : activatingKey ,
                                                     'CGI_URL'        : self.cfg.cgi_url() } 
                               )
                    
                    Transaction.create( os.path.join( sessionDir , self.FILENAME ) , 
                                        True ,  #authenticated
                                        False , #activated
                                        activatingKey = activatingKey , 
                                        userEmail = self.__userEmail , 
                                        passwd = cryptPasswd )
                    self.__generateTicketId()
                    # api create( id , authenticated , activated , activatingKey = None , userEmail = None, passwd = None)
                except MobyleError , err :
                    msg = "can't send an activation email, session creation aborted"
                    self.log.error( "%s : %s " % ( msg , err ) )
                    os.rmdir( self.Dir )
                    raise SessionError , msg
        self.url = "%s/%s/%s" % (self.cfg.user_sessions_url(), AuthenticatedSession.DIRNAME, self.key)

    def __generateTicketId( self , ticket_id=None):
        """
        create the ticket_id field in session file
        """
        self.ticket_id = ticket_id or str(random.randint(0, 1000000))
        transaction = self._getTransaction( Transaction.WRITE )
        transaction.setTicket( self.ticket_id, time() + 3600 )
        transaction.commit()
         
    def isAuthenticated( self ):
        return True   
    
    def setPasswd( self , passwd ):
        """
        set the pass word for this session
        @param passwd: the pass word to this session
        @type passwd: string
        """
        newMd5 = md5()
        newMd5.update( passwd )
        cryptPasswd = newMd5.hexdigest()
        transaction = self._getTransaction( Transaction.WRITE )
        transaction.setPasswd( cryptPasswd )
        transaction.commit()    
    
    
    def checkPasswd( self , passwd ):
        """
        check if passwd is the pass word of this session
        @param passwd: the session pass word
        @type passwd: string
        """
        if passwd == "":
            return False
        try:
            auth = policy_authenticate( self.__userEmail , passwd )
        except AttributeError:
            auth = self.CONTINUE
            
        if auth == self.VALID :
            return True
        elif auth == self.REJECT:
            return False
        else:
            transaction = self._getTransaction( Transaction.READ )
            realPasswd = transaction.getPasswd()
            transaction.commit()
        
            newMd5 = md5()
            newMd5.update( passwd )
            passwd = newMd5.hexdigest()
            if passwd == realPasswd :
                return True
            else:
                return False    

    def _getTicket( self ):
        """
        get the ticket
        @param ticket_id: the ticket_id
        @type ticket_id: string
        """
        transaction = self._getTransaction( Transaction.READ )
        r_ticket_id, r_exp_date = transaction.getTicket()
        transaction.commit()
        if time() < float(r_exp_date):
            self.__generateTicketId(r_ticket_id)
        else:
            self.__generateTicketId()
        return self.ticket_id
    
    def checkTicket( self , ticket_id ):
        """
        check if the ticket is valid
        @param ticket_id: the ticket_id
        @type ticket_id: string
        """
        transaction = self._getTransaction( Transaction.READ )
        r_ticket_id, r_exp_date = transaction.getTicket()
        transaction.commit()
        if r_ticket_id == ticket_id and time() < float(r_exp_date):
            transaction = self._getTransaction( Transaction.WRITE )
            transaction.setTicket( ticket_id, time() + 3600 )
            transaction.commit()            
            return True
        else:
            return False    


    
    def changePasswd( self , oldPasswd , newPasswd ):
        """
        change the password for this session
        @param oldPasswd: the current passwd
        @type oldPasswd: string
        @param newPasswd: the new passwd
        @type newPasswd: string
        @raise AuthenticationError: if oldPasswd 
        """
        newMd5 = md5()
        newMd5.update( oldPasswd )
        oldCryptPasswd = newMd5.hexdigest()
        
        newMd5 = md5()
        newMd5.update( newPasswd )
        newCryptPasswd = newMd5.hexdigest()
       
        transaction = self._getTransaction( Transaction.WRITE)
        currentPasswd = transaction.getPasswd()
                     
        if oldCryptPasswd == currentPasswd:
            transaction.setPasswd( newCryptPasswd )
            transaction.commit()
        else:
            transaction.rollback()
            raise AuthenticationError , "Authentication failure"
        
            
            
            
    def confirmEmail( self , userKey ):
        """
        if the activatingkey match the session activatingkey the session is activated
        @param userKey: the activation key send by email to the user
        @type userKey: string
        """ 
        transaction = self._getTransaction( Transaction.READ )
        activatingKey = transaction.getActivatingKey()
        transaction.commit()
        
        if userKey == activatingKey:
            transaction = self._getTransaction( Transaction.WRITE )
            transaction.activate()
            transaction.commit()
            self.log.debug("%f : %s : confirmEmail succeed : %s" % ( time(), self.getKey() , activatingKey ) )
        else:
            self.log.info("authentified/%s : wrong key : %s" % ( self.getKey() , activatingKey ) )
            raise AuthenticationError , "wrong key : %s" % activatingKey
        
             
    def __newSessionKey( self ):
        """
        @return: a unique id for the session
        @rtype: string
        """
        newMd5 = md5()
        newMd5.update( str( self.__userEmail ) )
        return newMd5.hexdigest()    
    
    
    def __newActivatingKey(self):
        """
        @return: a new Session uniq activating key
        @rtype: string
        """
        t1 = time()
        sleep( random.random() )
        t2 = time()
        base = md5( str(t1 +t2) )
        sid = base.hexdigest()
        return sid    
    
    
    def mergeWith( self , anonymousSession ):
        """
        merge an anonymous session to this authenticated session
        @param anonymousSession: the session to add this session
        @type anonymousSession: L{AnonymousSession} object
        """
        if anonymousSession == self:
            self.log.error( "authentified/%s try to merge with myself" % self.getKey() )
            raise SessionError , "try to merge with myself"   
        try:
            for data in anonymousSession.getAllData():
                self.addData( data['dataName'] ,  
                              data['Type'] , 
                              producer   = anonymousSession , 
                              inputModes = data['inputModes'] , 
                              usedBy     = data['usedBy'] , 
                              producedBy = data['producedBy']
                            )
            
            for job in anonymousSession.getAllJobs():
                self.addJob( job[ 'jobID' ] ,
                             userName = job[ 'userName' ] ,
                             dataUsed     = job[ 'dataUsed' ] ,
                             dataProduced = job[ 'dataProduced' ] 
                            )
        except Exception , err :
            self.log.error( "authentified/%s : error during mergeWith : %s" % ( self.getKey() , err ) )
            self.log.debug("%f : %s : error during mergeWith :" % ( time(), self.getKey() ) , exc_info = True )
            raise err
 
