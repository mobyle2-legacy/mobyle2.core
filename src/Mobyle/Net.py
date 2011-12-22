########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.        #
#                                                                                      #
########################################################################################


import smtplib
import mimetypes 
from email import Encoders
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.MIMEImage import MIMEImage
from email.MIMEText import MIMEText
import re
import os 
import types

from Mobyle.MobyleError import MobyleError , UserValueError , EmailError , TooBigError

import Local.black_list
import Local.Policy
import Local.mailTemplate

from logging import getLogger
n_log = getLogger( __name__ )

from Mobyle.ConfigManager import Config
cfg = Config()


def checkHost( ):

    try:
        userIP = os.environ[ 'REMOTE_ADDR' ]
    except KeyError:
        #MobyleJob is executed from commandline
        return True

    #rewriting the blacklist in a regexp
    pattern = '|'.join( Local.black_list.host )
    pattern = pattern.replace('.' , '\.' )
    pattern = pattern.replace('*' , '.*')
    pattern = "^(%s)$" % pattern
    auto = re.compile( pattern )

    if auto.search( userIP ):
        msg = "IP address is in black list"
        raise UserValueError( msg = msg )
    else:
        return True


class EmailAddress:
        
    INVALID = 0
    VALID = 1
    CONTINUE = 2
    
    def __init__( self , addr ):
        """
        @param addr: the emails addresses
        @type addr: string or list of strings
        """
        if not addr:
            raise MobyleError , 'addr must not be empty'
        if isinstance( addr , types.StringTypes ):
            self.addr = [ addr.strip() ]
        elif isinstance( addr , ( types.ListType , types.TupleType ) ):
            self.addr = addr 
        else:
            raise MobyleError , " addr must be a string or a list of strings : "+ str( addr )
        
        self._methods = [ self._checkSyntax ,
                          self._checkBlackList ,
                          self._checkLocalRules ]      
        
        if cfg.dnsResolver():
            self._methods.append( self._checkDns )
        
        self._message = ''        
    
    def __str__(self):
        return ','.join( self.addr )
    
    def getAddr(self):
        return [ addr for addr in self.addr ]
    
    
    def check( self ):
        """
        check if the addresses are valid:
         right syntax, 
         not in black list, 
         according to the local rules 
         and the domain have a mx fields)
        @return: True if the addresses pass the controls, False otherwise
        @rtype: boolean  
        """
        self._message = ''
        for oneAddr in self.addr:
            for method in self._methods:
                rep = method( oneAddr )
                if rep == self.VALID :
                    return True
                elif rep == self.INVALID :
                    return False
                elif rep == self.CONTINUE :
                    continue
                else:
                    raise MobyleError , method.__name__+ " return an invalid response :"+ str(rep)
        return True


    def getMessage( self ):
        return self._message
            
    def _checkSyntax( self , addr ):
        email_pat = re.compile( "^[a-z0-9\-\.+_]+\@([a-z0-9\-]+\.)+([a-z]){2,4}$" , re.IGNORECASE )
        match = re.match( email_pat , addr )

        if match is None:
            self._message = "invalid syntax for email address"
            return self.INVALID
        else:
            return self.CONTINUE


    def _checkBlackList( self , addr ):
        if addr in Local.black_list.users :
            self._message = "email is in black_list"
            return self.INVALID
        else:
            return self.CONTINUE


    def _checkLocalRules( self, addr  ):
        #tester si le module existe ? existe toujours meme si vide ?
        import Local.Policy
        rep = Local.Policy.emailCheck( email = addr )
        if rep == self.INVALID:
            self._message = "email is rejected by our local policy"
        return rep

    def _checkDns( self , addr ):
        import dns.resolver
        user , domainName  = addr.split('@')
        try:
            answers = dns.resolver.query( domainName , 'MX')
        except dns.resolver.NXDOMAIN , err :
            self._message = "unknown name domain"
            return self.INVALID
        except dns.resolver.NoAnswer ,err :
            try:
                answers = dns.resolver.query( domainName , 'A')
            except:
                self._message = "no mail server"
                return self.INVALID
            return self.CONTINUE
        except dns.name.EmptyLabel:
            self._message = "no domain name server"
            return self.INVALID
        except dns.exception.Timeout:
            self._message = "dns timeout"
            return self.INVALID
        except Exception, err:
            n_log.critical("unexpected error in  Email._checkDns : "+ str( err )  )
            return self.INVALID
        return self.CONTINUE
            
        
class Email: 
    
    def __init__( self , To , cc = None): 
        """
        @param To: the recipients addresses
        @type To: EmailAddress instance
        @param cc: the emails adresses in copy of this mail
        @type cc: EmailAddress instance
        """   
        self.To = To
        self.cc = cc
        self.mailhost = cfg.mailhost()
        self.headers = None
        self.body = None
        
    def getBody(self):
        return self.body
    
    def getHeaders(self):
        return self.headers
    
    def send( self , templateName , dict ,  files= None  ):
        """
        send an email to the Email.To recipients, using the template to build email body.
        @param template: the template of the mail. see Local/mailTemplate.py
        @type template: string 
        @param dict: the dictionnary used to expend the template
        @type dict: dictionnary
        @param files: the list of file names to attach to this email
        @type files: list of strings 
        """
        
        try:
            template = getattr( Local.mailTemplate , templateName )
        except AttributeError ,err:
            msg = "error during template %s loading: err" %( templateName ,err )
            n_log.critical( msg )
            raise MobyleError , err 
        try:
            mail = template % dict
        except ( TypeError , KeyError ) , err:
            msg = "error during template %s expanding: %s. This mail sending is aborted" %( templateName , err )
            n_log.critical( msg )
            raise MobyleError , msg 
        if not mail and not files:
            errMsg = "no msg and no files for template %s send email aborted" % templateName
            n_log.warning( errMsg )
            return None
        
        mailAttr , msg = self._parse( mail )
        if files:
            emailBody = MIMEMultipart()
        else:
            emailBody = MIMEText( msg , 'plain' , 'utf-8')
        
        mailAttr[ 'To' ] = str( self.To )
        recipients = self.To.getAddr()
        if self.cc:
            recipients.extend( self.cc.getAddr() )
            emailBody[ 'Cc' ] = str( self.cc )
            
        for attr in mailAttr.keys():
            if attr == 'Reply-To':
                emailBody[ attr ] = ', '.join( mailAttr[ attr ] )
            elif attr == 'Cc' or attr == 'Bcc' :
                recipients.extend( mailAttr[ attr ] )
                emailBody[ attr ] = ', '.join( mailAttr[ attr ] )
            else:
                emailBody[ attr ] =  mailAttr[ attr ] 
        try:
            s = smtplib.SMTP( self.mailhost )
        except Exception , err:     
            #except smtplib.SMTPException , err:
            n_log.error( "can't connect to mailhost \"%s\"( check Local.Config.Config.py ): %s" %( self.mailhost , err ) )
            raise EmailError , err
        
        if files:
            emailBody.preamble = 'You will not see this in a MIME-aware mail reader.\n'
            # To guarantee the message ends with a newline
            emailBody.epilogue = ''            
            if msg :
                msg = MIMEText( msg  , 'plain' , 'utf-8' )
                emailBody.attach( msg )

            for filename in files:
                if not os.path.isfile( filename ):
                    continue
    
                # Guess the content type based on the file's extension.  Encoding
                # will be ignored, although we should check for simple things like
                # gzip'd or compressed files.
    
                ctype, encoding = mimetypes.guess_type( filename )
                if ctype is None or encoding is not None:
                    # No guess could be made, or the file is encoded (compressed), so
                    # use a generic bag-of-bits type.
                    ctype = 'application/octet-stream'
    
                maintype, subtype = ctype.split( '/' , 1 )
                if maintype == 'text':
                    fp = open( filename , 'r')
                    # Note: we should handle calculating the charset
                    msg = MIMEText( fp.read() , _subtype = subtype )
                    fp.close()
                elif maintype == 'image':
                    fp = open( filename , 'rb' )
                    msg = MIMEImage( fp.read() , _subtype = subtype )
                    fp.close()
                else:
                    if filename == 'index.xml':
                        fp = self._indexPostProcess()
                    else:
                        fp = open( filename , 'rb' )
                        
                    msg = MIMEBase( maintype , subtype )
                    msg.set_payload( fp.read() )
                    fp.close()
                    # Encode the payload using Base64
                    Encoders.encode_base64( msg )
    
                # Set the filename parameter
                msg.add_header( 'Content-Disposition' , 'attachment', filename = os.path.basename( filename) )
                emailBody.attach( msg )
        
        try:
            s.sendmail( mailAttr[ 'From' ] , recipients , emailBody.as_string() )
            s.quit()
        except smtplib.SMTPSenderRefused, err:
            if err.smtp_code == 552 :
                raise TooBigError , str( err )
            else:
                raise EmailError , err
        except smtplib.SMTPException , err:
            n_log.error( "can't send email : %s" % err )
            raise EmailError , err
                
        except Exception , err:    
            #except smtplib.SMTPException , err:
            n_log.error( "can't send email : %s" % err , exc_info = True)
            n_log.error( str( recipients ) )
            raise EmailError , err                
            
    def _parse(self , mail ):
        headers = {}
        mail = mail.split( '\n' )
        iterator = iter( mail )
        begin = False

        for line in iterator:
            if not (begin or line):
                begin = True
                continue

            splitedLine = line.split(':')
            fields = splitedLine[0].strip()
            value = ':'.join( splitedLine[1:] )
            if fields == 'From':
                value = value.split( ',' )
                try:
                    value = value[0].strip()
                except IndexError :
                    raise MobyleError, '"From:" field cannot be empty '
                if not value:
                    raise MobyleError, '"From:" field cannot be empty '
            elif fields in ( 'Reply-To' , 'Cc' , 'Bcc' ) :
                value = value.split( ',' )
                value = [ val.strip() for val in value if val.strip() ]
                if not value:
                    continue
            elif not fields:
                body = '\n'.join( iterator )
                break
            else:
                value = value.strip()
                if not value:
                    continue
            headers[ fields ] = value
        self.headers = headers
        self.body = body
        return   headers , body
