########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################


import os 
import sys
import fcntl
import pickle
from lxml import etree
from time import strptime , strftime , time , sleep
from logging import getLogger

from Mobyle.Parser import parseType
from Mobyle.Classes.DataType import DataTypeFactory
from Mobyle.MobyleError import MobyleError , SessionError , ParserError
#from Mobyle.Utils import indent, parse_xml_file
from Mobyle.Utils import indent
from Mobyle.Status import Status

class Transaction( object ):
    """
    This class defines a session, that stores all the information
    about a user that should be persistent on the server
    @author: Bertrand Neron
    @organization: Institut Pasteur
    @contact:mobyle@pasteur.fr
    """
    __ref = {}
    
    WRITE  = fcntl.LOCK_EX
    READ   = fcntl.LOCK_SH
    
    def __new__( cls , fileName , lockType ):
        if not cls.__ref.has_key( fileName ) :
            self = super( Transaction , cls ).__new__( cls )
            self._log = getLogger( 'Mobyle.Session.Transaction' )
            fileName = os.path.normpath( fileName )
            try:
                if lockType == self.READ :
                    self.__File = open( fileName , 'r' )
                elif lockType == self.WRITE :
                    self.__File = open( fileName , 'r+' )
                else:
                    raise MobyleError , 'invalid lockType : ' +  str( lockType )
            except IOError , err:
                msg = "can't open session %s : %s" % ( os.path.basename( os.path.dirname( fileName ) ) , err )
                self._log.critical( msg )
                raise SessionError , msg
            
            self.__lockType = lockType
            
            self._lock() #try to acquire a lock 
            #If I do not got a lock a IOError is raised
            try:
                parser = etree.XMLParser( no_network = False )
                #self._doc = parse_xml_file(self.__File,parser)
                self._doc = etree.parse( self.__File , parser )
                self._root = self._doc.getroot()
            except Exception , err:
                import shutil
                shutil.copy2( self.__File.name , "%s.copy.%d" %( self.__File.name , int( time() ) ))
                msg = " an error occured during the session %s parsing : %s " % ( os.path.basename( os.path.dirname( fileName ) ) , err )
                self._log.error( msg , exc_info = True )      
                raise SessionError , err
            
            self._modified = False
            cls.__ref[ self.__File.name ] = True
            return self
        else:
            raise SessionError , "try to open 2 transactions on the same file at the same time"
        
    
    
    @staticmethod    
    def create( fileName , authenticated , activated , activatingKey = None , userEmail = None , passwd = None):
        """
        create a minimal xml session 
        @param fileName: the absolute path of the xml session file
        @type fileName: string
        @param authenticated: True if the session is authenticated , false otherwise
        @type authenticated: boolean
        @param activated: True if the session is activated, False otherwise.
        @type activated: boolean
        @param activatingKey: the key send to the user to activate this session
        @type activatingKey: boolean
        @param userEmail: the userEmail of the user
        @type userEmail: string
        """
        id = os.path.basename( os.path.dirname( fileName ))
        if authenticated and not passwd:
            msg = "cannot create authenticated session %s for %s without passwd" % ( id , userEmail )
            raise SessionError, msg
        
        if not authenticated and passwd:
            msg = "cannot create anonymous session %s for %s with passwd" % ( id , userEmail )
            raise SessionError, msg
        
        if authenticated and not userEmail:
            msg = "cannot create authenticated session %s without userEmail" % ( id )
            raise SessionError, msg
        root = etree.Element( "userSpace" , id = id )
        #doc = etree.ElementTree( root )
        
        authenticatedNode = etree.Element( "authenticated" )
        if authenticated:
            authenticatedNode.text = 'true'
            ticketNode = etree.Element( "ticket" )
            ticket_idNode = etree.Element( "id" )
            exp_dateNode = etree.Element( "exp_date" )
            ticketNode.append( ticket_idNode )
            ticketNode.append( exp_dateNode )
            root.append( ticketNode )    
        else:
            authenticatedNode.text = 'false' 
        root.append( authenticatedNode )    
        
        activatedNode = etree.Element( "activated" )
        if activated:
            activatedNode.text = 'true'
        else:
            activatedNode.text = 'false' 
        root.append( activatedNode ) 
         
        if userEmail:
            emailNode = etree.Element( "email" )
            emailNode.text = str( userEmail )
            root.append( emailNode ) 
        if passwd:
            passwdNode = etree.Element( "passwd" )
            passwdNode.text = passwd
            root.append( passwdNode )             
        if activatingKey:
            activatingKeyNode = etree.Element( "activatingKey" )
            activatingKeyNode.text =  activatingKey  
            root.append( activatingKeyNode ) 

        if os.path.exists( fileName ):
            msg = "cannot create session %s, file already exists" % fileName
            raise SessionError, msg

        xmlFile = open( fileName , 'w' )
        xmlFile.write( etree.tostring( root , xml_declaration=True , encoding='UTF-8', pretty_print= True )) 
        xmlFile.close()        


    def _lock(self):
        """
        try to acquire a lock of self.__lockType on self.__File
        @raise IOError: when it could not acquire a lock
        """
        IGotALock = False
        ID = os.path.basename( os.path.dirname( self.__File.name ))
        self._log.debug( "%f : %s : _lock Type= %s ( call by= %s )"  %( time() ,
                                                                        ID,
                                                                        ( 'UNKNOWN LOCK', 'READ' , 'WRITE' )[ self.__lockType ] ,
                                                                        os.path.basename( sys.argv[0] ) ,
                                                                        ))
        for attempt in range( 4 ):
            try:             
                fcntl.lockf( self.__File , self.__lockType | fcntl.LOCK_NB )
                IGotALock  = True
                self._log.debug( "%f : %s : _lock IGotALock = True" %(time() , ID ))
                break
            except IOError , err:
                self._log.debug( "%f : %s : _lock IGotALock = False" %(time() , ID))
                sleep( 0.2 )

        if not IGotALock :
            self._log.error( "%s : %s" %( ID , err ) )
            self._log.debug( "%f : %s : _lock Type= %s ( call by= %s )"  %( time() ,
                                                                            ID ,
                                                                            ( 'UNKNOWN LOCK', 'READ' , 'WRITE' )[ self.__lockType ] ,
                                                                            os.path.basename( sys.argv[0] ) 
                                                                            ))
            self.__File.close()
            self.__File = None
            self.__lockType = None
               
            raise IOError , err
    
    def _setModified(self , modified ):
        """
        to avoid that a 1rst method set modified to True and a 2 method reset it to False
        """
        if self._modified is False:
            self._modified = modified
    
    def _decodeData( self , data ):
        """
        convert the data in right encoding and replace windows end of line by unix one.
        """
        # trying to guess the encoding, before converting the data to ascii
        try:
            # trying ascii
            data = unicode(data.decode('ascii','strict'))
        except:
            try:
                # utf8 codec with BOM support
                data = unicode(data,'utf_8_sig')
            except:
                try:
                    # utf16 (default Windows Unicode encoding)
                    data = unicode(data,'utf_16')
                except:
                    # latin1
                    data = unicode(data,'latin1')
        # converting the unicode data to ascii
        data = data.encode('ascii','replace')   
        return data
         
    def _addTextNode( self, node , nodeName , content , attr = None):
        """ 
        add a text node named nodeName with content to the node node
        @param node: the node on which the new node will append 
        @type node: node element
        @param nodeName: the name of the new node
        @type nodeName: string
        @param content: the content of the new node
        @type content: string
        """
        newNode = etree.Element( nodeName )
        if attr:
            for attrName in attr.keys():
                newNode.set( attrName , str( attr[ attrName ] ) )
        try:
            newNode.text = content
        except Exception:
            data = self._decodeData( content )
            try:
                newNode.text = data
            except Exception:
                if nodeName != 'headOfData':
                    self._log.error( "%s :node = %s have not printable characters they will be replaced by'_': %s "  %(
                                                                                                                         self.getID() ,
                                                                                                                         nodeName 
                                                                                                                         ) )
                from string import printable
                for char in data :
                    if char not in printable :
                        data = data.replace( char , '_')
                try:
                    newNode.text =  data
                except Exception, err:
                    self._log.warning( "%s : cannot add text to textNode nodeName= %s : %s "  %(
                                                                                                 self.getID() ,
                                                                                                 nodeName ,
                                                                                                 err ,
                                                                                                ) )
                    newNode.text = '--- not printable ---'
        node.append( newNode )
    
    def _updateNode( self, node , nodeName , content ):
        """
        replace the content of the text_node child of a node by content. if the node nodeName doesn't exist, it make it
        @param nodeName: the name of the Node to update
        @type nodeName: String
        @param content: the content of the text-node child of nodeName
        @type content: String
        """
        node2update = node.find( "./" + nodeName )
        if node2update is not None:
            if node2update.text == content:
                return False
            else:
                node2update.text = str( content )
                return True
        else:
            newNode = etree.Element( nodeName )
            newNode.text = str( content )
            node.append( newNode )
            return True
    
    
    def commit(self):
        """
        if the transaction was open in WRITE
         - write the dom in xml file if it was modified 
        and release the lock and close the session File this transaction could not be used again
        """
        if self.__lockType == self.READ :
            logType = 'READ'
        elif self.__lockType == self.WRITE :
            logType = 'WRITE'
        else:
            logType = 'UNKNOWN LOCK( ' + str( self.__lockType ) +' )'

        self._log.debug( "%f : %s : _commit Type= %s ( call by= %s )"  %( time(),
                                                                         self.getID() ,
                                                                         logType ,
                                                                         os.path.basename( sys.argv[0] ) 
                                                                         ))
        try:
            if self.__lockType == self.WRITE and self._modified :
                try:
                    tmpFile = open( "%s.%d" %( self.__File.name , os.getpid() )  , 'w' )
                    indent( self._root )
                    tmpFile.write( etree.tostring( self._doc , xml_declaration=True , encoding='UTF-8'))
                    tmpFile.close()
                    os.rename( tmpFile.name , self.__File.name )
                except IOError , err:
                    msg = "can't commit this transaction: " + str( err )
                    self._log.error( msg )
                    raise SessionError , msg
                except Exception , err:
                    self._log.error( "session/%s self.__File = %s" %( self.getID(), self.__File ) , 
                                 exc_info = True )
                    raise err
        finally:
            key2del = self.__File.name 
            try:
                self._log.debug("%f : %s : commit UNLOCK type= %s modified = %s" %(time() ,
                                                                                          self.getID() ,
                                                                                          logType, 
                                                                                          self._modified
                                                                                          ))   
                fcntl.lockf( self.__File , fcntl.LOCK_UN  )
                self.__File.close()
                self.__File = None
                self.__lockType = None
                self._modified = False #reset _modifiedTransaction to false for the next transaction
                del( Transaction.__ref[ key2del ] )
            except IOError , err :
                self._log.error( "session/%s : cannot UNLOCK  transaction type= %s modified= %s: %s" %(self.getID(),
                                                                                                            logType,
                                                                                                            self._modified,
                                                                                                            err ) ) 
                del( Transaction.__ref[ key2del ] )

                
    def rollback(self):
        """
        release the lock , close the file without modification of the xml file.
        this transaction could not be used again
        """
        if self.__lockType == self.READ :
            logType = 'READ'
        elif self.__lockType == self.WRITE :
            logType = 'WRITE'
        else:
            logType = 'UNKNOWN LOCK( ' + str( self.__lockType ) +' )'

        self._log.debug( "%f : %s : _close Type= %s ( call by= %s )"  %( time(),
                                                                         self.getID() ,
                                                                         logType ,
                                                                         os.path.basename( sys.argv[0] ) 
                                                                         ))
        try:
            key2del = self.__File.name 
            sys.stdout.flush()
            fcntl.lockf( self.__File , fcntl.LOCK_UN  )
            self.__File.close()
            self.__File = None
            self.__lockType = None
            self._modified = False
            self._modified = False
        except IOError , err :
            self._log.error( "session/%s : an error occured during closing transaction : %s" %( self.getID() , err )) 
            # a gerer   
        except Exception , err :
            msg = "session/%s : an error occured during closing transaction : %s" % ( self.getID() , err )
            self._log.error( msg ) 
            self._log.debug( "%f : %s : self.__File = %s" %(time() , self.getID(), self.__File ))
            self._log.debug( "%f : %s : self.__lockType = %s" %(time() , self.getID(), logType ))
            raise SessionError , msg
        finally:
            try:
                del( Transaction.__ref[ key2del ] )
            except :
                pass
            
    def getID(self):
        """
        @return: the id of the session
        @rtype: string
        """
        id = self._root.get( 'id' )
        if id:
            return id
        else:
            msg = "the session %s has no identifier" % self.__File.name
            self._log.error( msg )
            raise SessionError , msg   
   
    def getEmail(self):
        """
        @return: the email of the user session
        @rtype: string 
        """
        try:
            return self._root.find( 'email' ).text
        except AttributeError:
            return None
        
    def setEmail( self , email ):
        """
        set the user email of this session 
        @param email: the email of the user of this session
        @type email: string
        """
        modified = self._updateNode( self._root , 'email' ,  email )
        self._setModified( modified )
        
        
    def isActivated( self ):
        """
        @return: True if this session is activated, False otherwise.
        @rtype: boolean
        """
        try:
            activated = self._root.find( 'activated' ).text
            if activated == 'true':
                return True
            else:
                return False
        except AttributeError:
            msg = "the session %s has no tag 'activated'" % self.__File.name
            self._log.error( msg )
            raise SessionError , msg
    
    def activate(self):
        """
        activate this session
        """
        modified = self._updateNode( self._root , 'activated' ,  'true' )
        self._setModified( modified )

    def inactivate(self):
        """
        activate this session
        """
        modified = self._updateNode( self._root , 'activated' ,  'false' )
        self._setModified( modified )
        
    def getActivatingKey(self):
        """
        @return: the key needed to activate this session ( which is send by email to the user )
        @rtype: string
        """
        try:
            return self._root.find( 'activatingKey' ).text
        except AttributeError:
            return None
    
    def isAuthenticated(self):
        """
        @return: True if this session is authenticated, False otherwise.
        @rtype: boolean
        """
        try:
            auth = self._root.find( 'authenticated').text
            if auth == 'true':
                return True
            else:
                return False
        except AttributeError:
            return None
    
    def getPasswd(self):
        """
        @return: the password of the user ( encoded )
        @rtype: string
        """
        try:
            return self._root.find( 'passwd' ).text
        except AttributeError:
            return None
    
    def setPasswd( self , passwd ):
        """
        set the session user pass word to passwd
        @param passwd: the encoded user password
        @type passwd: string
        """
        modified = self._updateNode( self._root , 'passwd' ,  passwd )
        self._setModified( modified )

    def getTicket(self):
        """
        get the currently allocated ticket and its expiration date
        @return: the ticket of the user and the expiration date
        @rtype: tuple
        """
        try:
            tck = self._root.find( 'ticket' )
            ticket_id = tck.find('id').text
            exp_date = tck.find('exp_date' ).text
            return (ticket_id, exp_date)
        except AttributeError:
            return None
    
    def setTicket( self , ticket_id, exp_date ):
        """
        set the currently allocated ticket and its expiration date
        @param ticket_id: the ticket
        @type ticket_id: string
        @param exp_date: the expiration date
        @type exp_date: date
        """
        tck = self._root.find( 'ticket' )
        if tck is not None:
            m1 = self._updateNode(tck, 'id', ticket_id)
            m2 = self._updateNode(tck, 'exp_date', exp_date)
            modified = m1 or m2
            self._setModified( modified )
        else:
            msg = "try to set id and exp-date to a ticket but ticket tag does not exist (%s)" % self.__File.name
            self._log.error( msg )
            raise SessionError , msg   
        
    def getCaptchaSolution( self ):
        """
        @return: the solution of the captcha problem submitted to the user.
        @rtype: string
        """
        try:
            return self._root.find( 'captchaSolution' ).text
        except AttributeError:
            return None
    
    def setCaptchaSolution( self  , solution ):
        """
        store the solution of the captcha problem submitted to the user.
        @param solution: the solution of the captcha
        @type solution: string
        """
        modified = self._updateNode( self._root , 'captchaSolution' ,  solution )
        self._setModified( modified )
    
    
    ################################
    #
    #  operations on Data
    #
    #################################
    def hasData(self , dataID ):
        """
        @param dataID: the identifier of the data in the session ( mdm5 name + ext )
        @type dataID: string
        @return: True if the session structure has an entry for the data corresponding to this ID, False otherwise.
        @rtype: boolean 
        """
        try:
            self._root.xpath( 'dataList/data[@id = "%s"]'% dataID )[0]
            return True
        except IndexError:
            return False 
            
    def renameData( self , dataID  , newUserName ):
        """
        change the user name of the data corresponding to the dataID.
        @param dataID: the identifier of the data in the session ( mdm5 name + ext )
        @type dataID: string
        @param newUserName: the new user name of the data.
        @type newUserName: string
        @raise ValueError: if dataID does not match any entry in session.
        """
        dataNode = self._getDataNode( dataID )
        modified = self._updateNode( dataNode , 'userName' ,  newUserName )
        self._setModified( modified )
    
    def getData(self , dataID ):
        """
        @param dataID: the identifier of the data in the session ( mdm5 name + ext )
        @type dataID: string
        @return: the data corresponding to the dataID
        @rtype: { 'dataName'   =  string ,
                  'userName'   =  string ,
                  'size'       =  int ,
                  'Type'       =  Mobyletype instance,
                  'dataBegin'    =  string ,
                  'inputModes' = [ string inputMode1 , string inputMode2 ,... ],
                  'producedBy' = [ string jobID1 , string jobID2 , ... ],  
                  'usedBy'     = [ string jobID1 , string jobID2 , ... ]
                  }
        @raise ValueError: if dataID does not match any entry in session.
        """
        dataNode = self._getDataNode( dataID )
        dtf = DataTypeFactory()
        return self._dataNode2dataDict( dataNode , dtf )

             
    def getAllData(self):
        """
        @return: all data in this session
        @rtype: [ {'dataName'   =  string ,
                  'userName'   =  string ,
                  'size'       =  int ,
                  'Type'       =  Mobyletype instance,
                  'dataBegin'    =  string ,
                  'inputModes' = [ string inputMode1 , string inputMode2 ,... ],
                  'producedBy' = [ string jobID1 , string jobID2 , ... ],  
                  'usedBy'     = [ string jobID1 , string jobID2 , ... ]
                  } , ... ]
        """
        datas = []
        dtf = DataTypeFactory()
        for dataNode in self._root.xpath( 'dataList/data') :
            data = self._dataNode2dataDict( dataNode , dtf )
            datas.append( data )
        return datas


    def removeData(self , dataID ):
        """
        remove the data entry corresponding to dataID
        @param dataID: the identifier of the data in the session ( mdm5 name + ext )
        @type dataID: string
        @raise ValueError: if dataID does not match any entry in session.
        """
        dataNode = self._getDataNode( dataID )
        dataListNode = dataNode.getparent()
        dataListNode.remove( dataNode )
        ## remove the ref of this data from the jobs
        usedBy = dataNode.xpath('usedBy/@ref' )
        for jobID in usedBy:
            try:
                jobNode = self._getJobNode( jobID )
            except ValueError:
                continue
            else:
                try:
                    dataUsedNode = jobNode.xpath( 'dataUsed[@ref="%s"]' %dataID )[0]
                except IndexError:
                    continue
                else:
                    jobNode.remove( dataUsedNode )
            
        producedBy = dataNode.xpath('producedBy/@ref' )
        for jobID in producedBy:    
            try:
                jobNode = self._getJobNode( jobID )
            except ValueError:
                continue
            else:
                try:
                    dataProducedNode = jobNode.xpath( 'dataProduced[@ref="%s"]' %dataID )[0]
                except IndexError:
                    continue
                else:
                    jobNode.remove( dataProducedNode )            
        self._setModified( True ) 
    
    
    def linkJobInput2Data(self , datasID ,  jobsID ):
        """
        add a ref of each job using this data and a ref of this data in the corresponding job
        @param datasID: the IDs of data which are used by these jobsID
        @type datasID: list of string
        @param jobsID: the IDs of job which has used these data
        @type jobsID: list of string
        @raise ValueError: if one dataID or jobID does not match any entry in session.
        """
        for dataID in datasID:
            dataNode = self._getDataNode( dataID )
            for jobID in jobsID :
                alreadyUsedBy = dataNode.xpath('usedBy/@ref' )
                if  jobID not in alreadyUsedBy :
                    newUsedByNode = etree.Element( 'usedBy' , ref = jobID )
                    dataNode.append( newUsedByNode )
                    self._setModified( True )
                try:
                    jobNode = self._getJobNode( jobID )
                except ValueError:
                    continue
                dataUsed = jobNode.xpath( 'dataUsed/@ref' )
                if dataID not in dataUsed:
                    newDataUsedNode = etree.Element( 'dataUsed' , ref = dataID )
                    jobNode.append( newDataUsedNode )
                    self._setModified( True )
    
    
    def linkJobOutput2Data(self , datasID , jobsID ):
        """
        add a ref of each job producing these data and a ref of these data in corresponding jobs.
        @param dataID: the list of the data ID
        @type dataID: list of string
        @param jobsID: the IDs of job which has produced this data
        @type jobsID: list of string
        @raise ValueError: if one dataID or jobID does not match any entry in session.
        """
        for dataID in datasID:
            dataNode = self._getDataNode( dataID )
            for jobID in jobsID:
                alreadyDataProduced = dataNode.xpath('producedBy/@ref' )
                if jobID not in alreadyDataProduced :
                    newUsedByNode = etree.Element( 'producedBy' , ref = jobID)
                    dataNode.append( newUsedByNode )
                    self._setModified( True )
                try:
                    jobNode = self._getJobNode( jobID )
                except ValueError:
                    continue
                dataProduced = jobNode.xpath( 'dataProduced/@ref' ) 
                if dataID not in dataProduced:
                    newDataProducedNode = etree.Element('dataProduced' , ref = dataID )
                    jobNode.append( newDataProducedNode )
                    self._setModified( True )

                
    def addInputModes(self , dataID , inputModes ):
        """
        add an inputmode in the list of inputModes of the data corresponding to the dataID
        @param dataID: The identifier of one data in this session
        @type dataID: string
        @param inputModes: the list of inputMode to add the accepted value are 'db' , 'paste' , 'upload' , 'result'
        @type inputModes: list of string
        @raise ValueError: if dataID does not match any entry in session.
        """
        dataNode = self._getDataNode( dataID )
        modesNode = dataNode.find( 'inputModes')
        if modesNode is not None:
            oldModes = modesNode.xpath( 'inputMode/text()') 
        else:
            modesNode = etree.Element( 'inputModes' )
            oldModes = []
        for newMode in inputModes:
            if newMode in oldModes:
                continue
            else:
                newInputNode = etree.Element( 'inputMode' )
                newInputNode.text = newMode
                modesNode.append( newInputNode )
                self._setModified( True )
     
     
    def createData( self , dataID , userName , size , mobyleType , dataBegining , inputModes , producedBy = [] , usedBy = []):
        """
        add a new data entry in the session.
        @param dataID: The identifier of one data in this session
        @type dataID: string
        @param userName: the name given by the user to this data
        @type userName: string
        @param size: the size of the file corresponding to this data
        @type size: int
        @param Type: the MobyleType of this data
        @type Type: L{MobyleType} instance
        @param dataBegining: the 50 first char of the data (if data inherits from Binary a string)
        @type dataBegining: string
        @param inputModes: the input modes of this data the accepted data are: 'paste' , 'db' , 'upload' , 'result'
        @type inputModes: list of string
        @param format: the format , count , of this data
        @type format: ( string format , int count , string 'to fill the api (unused)' )
        @param producedBy: the jobs Id which produced this data
        @type producedBy: list of string
        @param usedBy: the jobs ID which used this data
        @type usedBy: list of string
        """
        dataListNode = self._root.find( 'dataList')
        if dataListNode is None:
            dataListNode = etree.Element( 'dataList')
            self._root.append( dataListNode )
        dataNode = etree.Element( 'data' , id =  dataID , size = str( size ))
        self._addTextNode( dataNode , "userName" ,  userName )
        typeNode = mobyleType.toDom()
        dataNode.append( typeNode )
        self._addTextNode( dataNode , "headOfData" ,  dataBegining )
        
        if inputModes:   
            inputModesNode = etree.Element( 'inputModes' )
            for inputMode in inputModes:
                self._addTextNode( inputModesNode , "inputMode" ,  inputMode )
                dataNode.append( inputModesNode )
        
        for jobId in producedBy:
            producedByNode = etree.Element( "producedBy" , ref = jobId )
            dataNode.append( producedByNode )
        for jobId in usedBy:
            usedByNode = etree.Element( "usedBy" , ref = jobId )
            dataNode.append( usedByNode )           
        dataListNode.append( dataNode )  
        self._setModified( True )

    def addWorkflowLink( self , id):
        """
        add a new workflow definition in the session.
        @param id: The identifier of the workflow
        @type id: string
        """
        workflowsListNode = self._root.find( 'workflowsLinkList')
        if workflowsListNode is None:
            workflowsListNode = etree.Element( 'workflowsLinkList')
            self._root.append( workflowsListNode )
        workflowNode = etree.Element( 'workflowLink' , id = str(id))
        workflowsListNode.append( workflowNode )  
        self._setModified( True )

    def getWorkflows( self):
        """
        get the list of workflow definitions in the session.
        @return: workflow definition identifiers list
        @rtype: [ {'id':string } , ... ]

        """
        list = []
        for workflow in self._root.xpath( 'workflowsLinkList/workflowLink') :
            list.append(int(workflow.get('id')))
        return list
      
    def _getDataNode(self , dataID ):
        """
        @param dataID: the identifier of one data in this session
        @type dataID: string
        @return: the Node corresponding to the dataID
        @rtype: Node instance
        @raise ValueError: if dataID does not match any entry in this session.
        """
        try:
            dataNode = self._root.xpath( 'dataList/data[@id = "%s"]' % dataID )[0]
            return dataNode
        except IndexError:
            msg = "the data %s does not exist in the session %s" % ( dataID , self.getID() )
            raise ValueError , msg
               
                           
    def _dataNode2dataDict(self, dataNode , dtf ):
        """
        @param dataNode: a node representing a data
        @type dataNode: Node instance
        @param dtf: a dataTypeFactory
        @type dtf: a L{Mobyle.Classes.Core.DataType.DataTypeFactory} instance
        """
        data = {}
        data[ 'dataName' ] = dataNode.get( 'id' )
        try:
            data[ 'userName' ] = dataNode.find( 'userName' ).text
        except AttributeError:
            msg = "data %s has no userName" % data[ 'dataName' ]
            self._log.error( msg )
            SessionError , msg
        try:
            data[ 'Type' ] = parseType( dataNode.find( 'type' ) , dataTypeFactory = dtf )
        except ( ParserError , MobyleError ) :
            msg = "error in type parsing for data %s "% data[ 'dataName' ]
            self._log.error( msg , exc_info = True )
            raise SessionError , msg
        try:
            data[ 'dataBegin' ] = dataNode.find( 'headOfData').text
        except AttributeError:
            data[ 'dataBegin' ] = ''
        try:
            data[ 'inputModes' ] = [ inputmode.text  for inputmode  in dataNode.findall( 'inputModes/inputMode' ) ]
        except AttributeError:
            pass
        data[ 'producedBy' ] =  dataNode.xpath( 'producedBy/@ref' ) 
        data[ 'usedBy' ] = dataNode.xpath( 'usedBy/@ref' ) 
        data[ 'size' ] = int( dataNode.get( 'size' ) )
        return data 


    #####################
    #
    #   jobs methods
    #
    #####################

    def _get_userAnnotation_node(self , jobID ):
        """
        @return: the userAnnotationNode of job with jobID. 
        if userAnnotationNode doesnot exist make it
        @rtype: etree.element instance
        @param jobID: the job identifer (it's url) of a job
        @type jobID: string
        @raise ValueError: if there is no job with jobID in the session
        """
        jobNode = self._getJobNode( jobID )
        userAnnotation_node = jobNode.find( 'userAnnotation' )
        if userAnnotation_node is not None:
            self._setModified( False )
        else:
            userAnnotation_node = etree.Element( 'userAnnotation' )
            jobNode.append( userAnnotation_node )
            self._setModified( True )
        return userAnnotation_node

    def getAllUniqueLabels(self):
        labelsList = []
        #rather to use recursive search 
        #I used direct path from root
        for labelNode in self._doc.findall('/jobList/job/userAnnotation/labels/label') :
            if not labelNode.text in labelsList :
                labelsList.append( labelNode.text )
        return labelsList

    def getJobDescription( self, jobID):
        """
        @return: the description for job with identifier jobID
        @rtype: string or None if there is no description for this job 
        @param jobID: the job identifer (it's url) of a job
        @type jobID: string
        @raise ValueError: if there is no job with jobID in the session
        """
        user_annot_node = self._get_userAnnotation_node( jobID )
        try:
            description = user_annot_node.find( 'description' ).text 
            return  description
        except AttributeError:
            return None    

    def setJobDescription( self, jobID , description):
        """
        set description for the job with jobId
        @param jobID: the job identifer (it's url) of a job
        @type jobID: string
        @param description: the description of this job
        @type description: string
        @raise ValueError: if there is no job with jobID in the session
        """
        user_annot_node = self._get_userAnnotation_node( jobID )
        modified = self._updateNode( user_annot_node , 'description' ,  description )
        self._setModified( modified )
        
    def setJobLabels( self, jobID, inputLabels):
        """
        set labels for job with  jobId
        @param jobID: the job identifer (it's url) of a job
        @type jobID: string
        @param description: the description of this job
        @type description: string
        @raise ValueError: if there is no job with jobID in the session
        """
        user_annot_node = self._get_userAnnotation_node( jobID )
        labels_node = user_annot_node.find( 'labels' )
        if labels_node is not None:
            user_annot_node.remove( labels_node )
        new_labels_node = etree.Element( 'labels' )   
        for new_label in inputLabels:
            new_label_node = etree.Element( 'label' )
            new_label_node.text = new_label
            new_labels_node.append( new_label_node )
        user_annot_node.append( new_labels_node )
        self._setModified( True )   
            

    def getJobLabels( self, jobID):
        """
        @return: the labels for job with identifier jobID
        @rtype: list of strings , [ string label1 ,string label2 ,...] or None if this jobs has no labels. 
        @param jobID: the job identifer (it's url) of a job
        @type jobID: string
        @raise ValueError: if there is no job with jobID in the session
        """
        user_annot_node = self._get_userAnnotation_node( jobID )
        labels_node = user_annot_node.find( 'labels' )
        if labels_node is None:
            return []
        else:
            labels = [ labelNode.text  for labelNode in labels_node.findall( 'label' ) ]
        return labels
    
        
    def hasJob( self , jobID ):
        """
        @param jobID: the identifier of the job in the session ( the url without index.xml )
        @type jobID: string
        @return: True if the session structure has an entry for the job corresponding to this ID, False otherwise.
        @rtype: boolean 
        """
        try:
            self._root.xpath( 'jobList/job[@id="%s"]'% jobID )[0]
            return True
        except IndexError:
            return False 

    
    def getJob(self , jobID ):    
        """
        @param jobID: the identifier of the job in the session ( the url without index.xml )
        @type jobID: string
        @return: the job corresponding to the jobID
        @rtype: {'jobID'       : string ,
                 'userName'    : string ,
                 'programName' : string ,
                 'status'      : Status object ,
                 'date'        : time struct ,
                 'dataProduced': [ string dataID1 , string dataID2 , ...] ,
                 'dataUsed'    : [ string dataID1 , string dataID2 , ...] ,
                }
        @raise ValueError: if the jobID does not match any entry in this session
        """
        jobNode = self._getJobNode( jobID )
        return self._jobNode2jobDict( jobNode )

    
    def getAllJobs(self):
        """
        @return: the list of jobs in this session
        @rtype:  [ {'jobID'       : string ,
                    'userName'    : string ,
                    'programName' : string ,
                    'status'      : Status object ,
                    'date'        : time struct ,
                    'dataProduced': [ string dataID1 , string dataID2 , ...] ,
                    'dataUsed'    : [ string dataID1 , string dataID2 , ...] ,
                   } , ... ]
        """
        jobs = []
        jobList = self._root.findall( 'jobList/job' )
        for jobNode in jobList:
            job = self._jobNode2jobDict( jobNode )
            jobs.append( job )
        return jobs

    #OPENID
    def addOpenIdAuthData(self, authsession):
        """
        @param authsession: the session used by OpenId library
        @type authsession: Session
        @raise SessionError : if data cannot be saved
        """
        authNode = self._root.find( 'authOpenIdData' )
        if authNode:
            self._root.remove( authNode )
        authNode = etree.Element( 'authOpenIdData')

        for name in authsession.keys():
            self._addTextNode(authNode, name, pickle.dumps(authsession[name]))
        self._root.append(authNode)
        self._setModified( True )

    #OPENID
    def getOpenIdAuthData(self):
        """
        @return : Session with openid data
        @raise SessionError : if data cannot be read
        """
        authNode = self._root.find( 'authOpenIdData' )
        if not authNode:
            msg = "No auth data available"
            raise ValueError , msg
        authsession = {}
        #Parse sessionData to get name and value
        for child in authNode.getchildren():
            if(child.tag!="#text"):
                authsession[child.tag] = pickle.loads(child.text)
        return authsession

    def createJob(self , jobID , userName , programName , status , date , dataUsed ,  dataProduced ):
        """
        add a new job entry in this session
        @param jobID: the identifier of the job in the session ( the url without index.xml )
        @type jobID: string
        @param userName: the name of this job given by the user
        @type userName: string
        @param programName: the name of the program which generate this job
        @type programName: string
        @param status: the status of this job
        @type status: L{Status.Status} instance
        @param date: the date of job submission
        @type date: time struct 
        @param dataUsed: the list of data stored in this session used by this job.
        @type dataUsed: list of strings
        @param dataProduced: the list of data stored in this session and produced by this job.
        @type dataProduced: list of strings
        """
        jobListNode = self._root.find( 'jobList' )
        if jobListNode is None:
            jobListNode = etree.Element('jobList')
            self._root.append( jobListNode )
        jobexist = self._doc.xpath( 'jobList/job[@id="%s"]' % jobID )
        if jobexist:
            raise ValueError , "can't create a new job entry in session %s :the jobID %s already exist" % ( self.getID() , jobID ) 
        jobNode = etree.Element( 'job' , id = jobID )
        self._addTextNode( jobNode, 'userName' , userName )
        self._addTextNode( jobNode, 'programName' , programName )
        self._addTextNode( jobNode, 'date' , strftime( "%x  %X" , date ) )
        self._addTextNode( jobNode, 'status' , str( status ) ) 
        if status.message :
            self._addTextNode( jobNode, 'message' , status.message )
        
        for dataID in dataUsed:
            dataUsedNode = etree.Element( "dataUsed" , ref = dataID )
            jobNode.append( dataUsedNode )
        for dataID in dataProduced:
            dataProducedNode = etree.Element( "dataProduced" , ref = dataID )
            jobNode.append( dataProducedNode )     
        jobListNode.append( jobNode )
        self._setModified( True )
  
    
    def removeJob(self , jobID ):
        """
        remove the entry corresponding to this jobID 
        @param jobID: the identifier of the job in the session ( the url without index.xml )
        @type jobID: string
        @return: the job corresponding to jobID as a dict
        @rtype: dictionary
        @raise ValueError: if the jobID does not match any entry in this session
        """
        jobNode = self._getJobNode(jobID)
        jobDict = self._jobNode2jobDict( jobNode )
        jobListNode = jobNode.getparent()
        jobListNode.remove( jobNode )
        ## remove the ref of this job from the data
        dataUsedNodes = jobNode.findall( 'dataUsed' )
        for dataUsedNode in dataUsedNodes:
            dataID = dataUsedNode.get( 'ref' )
            try:
                dataNode = self._getDataNode( dataID )
            except ValueError:
                continue
            else:
                try:
                    usedByNode = dataNode.xpath( 'usedBy[@ref="%s"]' %jobID )[0]
                except IndexError:
                    continue
                else:
                    dataNode.remove( usedByNode )
            
        dataProducedNodes = jobNode.findall( 'dataProduced' )
        for dataProducedNode in dataProducedNodes:
            dataID = dataProducedNode.get( 'ref' )
            try:
                dataNode = self._getDataNode( dataID )
            except ValueError:
                continue
            else:
                try:
                    producedByNode = dataNode.xpath( 'producedBy[@ref="%s"]' %jobID )[0]
                except IndexError:
                    continue
                else:
                    dataNode.remove( producedByNode )
        self._setModified( True ) 
        return jobDict       

               
    def renameJob( self , jobID , newUserName ):
        """
        change the user name of the data corresponding to the dataID.
        @param jobID: the identifier of the job in the session ( url without index.xml )
        @type jobID: string
        @param newUserName: the new user name of the job.
        @type newUserName: string
        @raise ValueError: if jobID does not match any entry in session.        
        """
        jobNode = self._getJobNode( jobID )
        modified = self._updateNode( jobNode , 'userName' ,  newUserName )
        self._setModified( modified )
        
        
    def updateJobStatus( self , jobID , status ):
        """
        update the status of the job corresponding to the jobID
        @param jobID: the identifier of the job in the session ( url without index.xml )
        @type jobID: string
        @param status: the status of this job
        @type status: L{Status.Status} instance
        @raise ValueError: 
        """
        jobNode = self._getJobNode( jobID )
        modified = self._updateNode( jobNode , 'status' , str( status ) )
        if status.message:
            modified = self._updateNode( jobNode , 'message' , status.message )
        self._setModified( modified )
        
            
    def _getJobNode( self , jobID ):
        """
        @param jobID: the identifier of one job in this session
        @type jobID: string
        @return: the Node corresponding to the jobID
        @rtype: Node instance
        @raise ValueError: if jobID does not match any entry in this session.
        """
        try:
            return self._root.xpath( 'jobList/job[@id="%s"]' % jobID )[0]
        except IndexError:
            msg = "the job %s does not exist in the session %s" % ( jobID , self.getID() )
            raise ValueError , msg
                    
    
    def _jobNode2jobDict( self , jobNode ):
        """
        @param jobNode: a node representing a job
        @type jobNode: Node instance
        """
        job = {}
        job [ 'jobID' ] = jobNode.get( 'id' )
        try:
            job[ 'userName' ] = jobNode.find( 'userName' ).text
        except AttributeError:
            self._log.error( "the job %s in session %s has no userName" %( job[ 'jobID' ] , self.getID()) )
        try:
            job[ 'programName' ] =  jobNode.find( 'programName' ).text 
        except AttributeError :
            self._log.error( "the job %s in session %s has no programName" % ( job[ 'jobID' ] , self.getID()) )
        try:
            statusString = jobNode.find( 'status' ).text
        except AttributeError :
            msg = "the job %s in session %s has no status" % ( job[ 'jobID' ] , self.getID()) 
            self._log.error( msg )
            raise MobyleError( msg )
        else:
            try:
                message = jobNode.find( 'message' ).text
            except AttributeError:
                message = ''
            try:
                job[ 'status' ] = Status( string= statusString , message = message )
            except KeyError:
                msg = "error in status %s for job %s in session %s" % ( statusString ,
                                                                        job[ 'jobID' ] , 
                                                                        self.getID()
                                                                      ) 
                self._log.error( msg )
                raise MobyleError , msg
        
        try:
            job[ 'date' ] = strptime( jobNode.find( 'date' ).text , "%x  %X")
        except IndexError:
            pass  
        job[ 'dataProduced' ] =  jobNode.xpath( 'dataProduced/@ref' ) 
        job[ 'dataUsed' ] = jobNode.xpath( 'dataUsed/@ref' ) 
        return job 
       
       
       
