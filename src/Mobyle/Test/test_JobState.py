########################################################################################
#                                                                                      #
#   Author: Bertrand Neron,                                                            #
#   Organization:'Biological Software and Databases' Group, Institut Pasteur, Paris.   #  
#   Distributed under GPLv2 Licence. Please refer to the COPYING.LIB document.         #
#                                                                                      #
########################################################################################

import unittest2 as unittest
import os
import sys
import shutil
import time

MOBYLEHOME = os.path.abspath( os.path.join( os.path.dirname( __file__ ) , "../../../" ) )
os.environ['MOBYLEHOME'] = MOBYLEHOME

if ( MOBYLEHOME ) not in sys.path:
    sys.path.append( MOBYLEHOME )
if ( os.path.join( MOBYLEHOME , 'Src' ) ) not in sys.path:    
    sys.path.append( os.path.join( MOBYLEHOME , 'Src' ) )

import Mobyle.Test.MobyleTest
from lxml import etree
from Mobyle import JobState
from Mobyle.Utils import Status
from Mobyle.Service import MobyleType
from Mobyle.Classes.DataType import DataTypeFactory

DATADIR = os.path.dirname( __file__ )

class JobStateTest(unittest.TestCase):
    """Tests the functionalities of Transaction"""
    
    fake_mobyle_path = '/tmp/test_Mobyle'
    
    def setUp(self):
        """ 
        setting up the configuration for the test, including:
        - test configuration that does not check dns or try to send confirmation emails
        - test session email
        """
        self.cfg = Mobyle.ConfigManager.Config()
        self.cfg._root_url           = 'http://marygay.sis.pasteur.fr:82'
        self.cfg._results_path       = os.path.join( self.__class__.fake_mobyle_path , 'results' )
        self.cfg._results_url        = "%s%s" % ( self.cfg._root_url , '/mobyle/results')
        
        #create space for test
        if os.path.exists( self.__class__.fake_mobyle_path ):
                    shutil.rmtree( self.__class__.fake_mobyle_path )
        os.makedirs( self.__class__.fake_mobyle_path )

        #create jobs directory
        if os.path.exists( self.cfg.results_path() ):
                    shutil.rmtree( self.cfg.results_path() )
        os.makedirs( self.cfg.results_path() )
        
        
        self.jobID = [ self.cfg.results_url() + "/fake_job/A00000000000000",
                       self.cfg.results_url() + "/fake_job/A00000000000001" 
                       ]
        
        self.jobs = [ {'jobID'       :  self.jobID[0] ,
                       'name'        : 'http://marygay.sis.pasteur.fr:81/mobyle/programs/dnadist.xml' ,
                       'host'        : 'http://marygay.sis.pasteur.fr:81' ,
                       'status'      :  Status( code = 6 ),#'killed' ,
                       'date'        :  time.strptime( "11/20/08  12:00:00", "%x  %X"),#(2008, 11, 20, 12, 0, 0, 3, 325, -1),
                       'dataProduced': [] ,
                       'dataUsed'    : ['16bd6f89e732eb7cb0bbc13c65d202d3.aln'] ,
                       'sessionKey'  : 'R18991749411106',
                       'email'       : 'bneron@pasteur.fr',
                       'args'        : {'infile': 'clustal.aln', 'seqboot': 'True', 'replicates': '50', 'seqboot_seed': '3'} ,
                       'commandLine' : 'ln -s clustal.aln infile &amp;&amp; seqboot &lt; seqboot.params &amp;&amp; mv outfile seqboot.outfile &amp;&amp; rm infile &amp;&amp;ln -s seqboot.outfile infile &amp;&amp; dnadist &lt;dnadist.params &amp;&amp; mv outfile dnadist.outfile' ,
                       'formattedData': {'infile': {'formattedFile': None, 'fileFmt': 'PHYLIPI', 'fmtprogram': 'squizz', 'file': 'clustal.aln', 'formattedFileFmt': None}} ,
                       'paramfiles'  : [('seqboot.params', 11L), ('dnadist.params', 11L)],
                      } ,
                      {'jobID'       : self.jobID[1] ,
                       'name'        : 'http://marygay.sis.pasteur.fr:81/mobyle/programs/dnadist.xml' ,
                       'host'        : 'http://marygay.sis.pasteur.fr:81' ,
                       'status'      :  Status( code = 4 ),#finished Status( code = 3 ),#running
                       'date'        :  time.strptime( "11/19/08  10:50:33", "%x  %X"),#(2008, 11, 19, 10, 50, 33, 2, 324, -1),
                       'dataProduced': ['f835ddf28cb6aa776a41d7c71ec9cb5a.out'] ,
                       'dataUsed'    : ['16bd6f89e732eb7cb0bbc13c65d202d3.aln'] ,
                       'sessionKey'  : 'R18991749411106',
                       'email'       : 'bneron@pasteur.fr',
                       'args'        : {'infile': 'clustal.aln', 'seqboot': 'True', 'replicates': '10', 'seqboot_seed': '3'} ,
                       'commandLine' : 'n -s clustal.aln infile &amp;&amp; seqboot &lt; seqboot.params &amp;&amp; mv outfile seqboot.outfile &amp;&amp; rm infile &amp;&amp;ln -s seqboot.outfile infile &amp;&amp; dnadist &lt;dnadist.params &amp;&amp; mv outfile dnadist.outfile' ,
                       'formattedData': {'infile': {'formattedFile': None, 'fileFmt': 'PHYLIPI', 'fmtprogram': 'squizz', 'file': 'clustal.aln', 'formattedFileFmt': None}} ,
                       'paramfiles'  : [('seqboot.params', 11L), ('dnadist.params', 11L)],
                       },
                       ]
        self.jobDir = self._makeFakeJob( self.jobID[1] )
        self.jobState = JobState.JobState( self.jobDir )
        
    def testgetOutputs( self ):    
        outputs_recieved = self.jobState.getOutputs()
        outputs = [( "P1", 
                           [('dnadist.outfile', 206400L, 'None')]), 
                    ("P2", 
                           [('seqboot.outfile', 976580L, 'None')]), 
                    ("P3", 
                            [('dnadist.out', 25411L, 'None')])]
        self.assertTrue( len( outputs_recieved ) == 3 )
                 
    def testgetOutput( self ):    
        output_recieved = self.jobState.getOutput( 'seqboot_out' )
        self.assertEqual( output_recieved , [('seqboot.outfile', 976580L, None)] )
        
    def testgetInputFiles( self ):   
        inputs_recieved = self.jobState.getInputFiles()
        inputs = [("P1", [('clustal.aln', 90044L, 'PHYLIPI')])]
        
    def testgetDir( self ):    
        self.assertEqual( self.jobState.getDir() , self.jobDir )
    
    def testID( self ):    
        self.jobState.setID( self.jobID[0])
        self.jobState.commit()
        self.assertEqual( self.jobState.getID() , self.jobID[0] )
        self.jobState.setID( self.jobID[1])
        self.jobState.commit()
        
    def testSessionKey( self ):    
        self.jobState.setSessionKey( self.jobs[0][ 'sessionKey' ])
        self.jobState.commit()
        self.assertEqual( self.jobState.getSessionKey() , self.jobs[0][ 'sessionKey' ] )
                          
    def testCommandLine( self ):    
        self.jobState.setCommandLine( self.jobs[0][ 'commandLine' ])
        self.jobState.commit()
        self.assertEqual( self.jobState.getCommandLine() , self.jobs[0][ 'commandLine' ] )
    
    def testName( self ):    
        self.jobState.setName( self.jobs[0][ 'name' ])
        self.jobState.commit()
        self.assertEqual( self.jobState.getName() , self.jobs[0][ 'name' ] )
    
    def testDate( self ):    
        self.jobState.setDate( self.jobs[0][ 'date' ])
        self.jobState.commit()
        self.assertEqual( self.jobState.getDate() , time.strftime( "%x  %X" , self.jobs[0][ 'date' ] ) )
    
    def testEmail( self ):    
        self.jobState.setEmail( self.jobs[0][ 'email' ])
        self.jobState.commit()
        self.assertEqual( self.jobState.getEmail() , self.jobs[0][ 'email' ] )
    
    def testgetStdout( self ): 
        stdout_file = open( os.path.join( self.jobDir , os.path.basename( self.jobState.getName()))[:-4]+".out" )
        stdout = ''.join( stdout_file.readlines() )
        stdout_file.close()
        self.assertEqual( self.jobState.getStdout() , stdout )
        
    def testgetOutputFile( self ):    
        fileName = "dnadist.outfile"
        File = open( os.path.join( self.jobDir , fileName ) )
        content  = ''.join( File.readlines() )
        File.close()
        self.assertEqual( self.jobState.getOutputFile( fileName ) , content )
        
#    def testopen( self ):    
#        pass
#    
    def testgetStderr( self ):    
        stderr_file = open( os.path.join( self.jobDir , os.path.basename( self.jobState.getName()))[:-4]+".err" )
        stderr = ''.join( stderr_file.readlines() )
        stderr_file.close()
        self.assertEqual( self.jobState.getStderr() , stderr )
    
    def testsetHost( self ):
        sent_host =  'http://foo.bar.pasteur.fr'   
        self.jobState.setHost( sent_host )
        self.jobState.commit()
        doc = etree.parse( self.jobDir + "/index.xml" )
        recieved_host = doc.find( 'host' ).text
        self.assertEqual( recieved_host , sent_host )
    
    def testsetInputDataFile( self ): 
        dtf = DataTypeFactory()
        self.dataType1 = dtf.newDataType( 'Text' )
        dataFile = {  
                    'paramName'   : "in_param_file",
                    'File'        : ( 'foo.ori' , 'beautiful.format' , 234 ) ,
                    'fmtProgram'  : 'squizz',
                    'formattedFile': ( 'foo.reformat' , 'wonderful.format' , 432 ) ,
                    }   
        self.jobState.setInputDataFile( dataFile[ 'paramName' ] ,
                                        dataFile[ 'File' ],
                                        dataFile[ 'fmtProgram' ] ,
                                        dataFile[ 'formattedFile' ],
                                         )
        self.jobState.commit()
        tree = etree.parse( os.path.join( os.path.join( self.jobDir , 'index.xml') ))
        root = tree.getroot()
        param = root.xpath( 'data/input/parameter[ name = "'+ dataFile[ 'paramName' ] + '" ]')[0]                    
        self.assertEqual( param.find( 'name' ).text , dataFile[ 'paramName' ] )
        
#    def testrenameInputDataFile( self ):    
#        pass
#    
#    def testsetInputDataValue( self ):    
#        pass
#    
#    def testsetOutputDataFile( self ):    
#        pass
#    
#    def testdelInputData( self ):    
#        pass
#    
    def testgetArgs( self ): 
        self.assertEqual( self.jobState.getArgs() , self.jobs[1]['args'] )

    
    def testgetPrompt( self ):    
        prompt = "Perform a bootstrap before analysis"
        self.assertEqual( self.jobState.getPrompt( 'seqboot' ) , prompt )     
        
    def testgetFormattedData( self ):    
        self.assertEqual( self.jobState.getFormattedData() , self.jobs[1]['formattedData'] )
    
    def testParamfiles( self ):
        self.assertEqual( self.jobState.getParamfiles() , self.jobs[1]['paramfiles'] )
        new_paramfiles = ( 'test' , 22L )
        self.jobs[1]['paramfiles'].append( new_paramfiles )
        self.jobState.setParamfiles( [ new_paramfiles ] )
        self.jobState.commit()
        self.assertEqual( self.jobState.getParamfiles() ,  self.jobs[1]['paramfiles'] )
        
    def _makeFakeJob(self , jobID ):
        jobPath = JobState.url2path( jobID ) 
        jobdir = os.path.dirname( jobPath )
        if not os.path.exists( jobdir ):
            os.makedirs( jobdir , 0755)
            
        if os.path.exists( jobPath ):
            shutil.rmtree( jobPath )
        index = jobID[-1]
        
        shutil.copytree( os.path.join( DATADIR , 'fake_job' + index ) , jobPath )
        
        doc = etree.parse( os.path.join( jobPath , 'index.xml' ) )
        root = doc.getroot()
        
        nameNode = root.find( 'name' )
        nameNode.text = self.cfg.repository_url() + '/fake.xml'
        
        hostNode = root.find( 'host' )
        hostNode.text = self.cfg.root_url()
        
        idNode   = root.find( 'id' )
        idNode.text = jobID
        
        xmlfile = open(  os.path.join( jobPath , 'index.xml' ) , 'w' )
        xmlfile.write( etree.tostring( doc , xml_declaration=True , encoding='UTF-8', pretty_print= True ) )
        xmlfile.close()
        
        return jobPath
    
#    @classmethod
#    def tearDownClass( cls ):
#        shutil.rmtree( cls.fake_mobyle_path , ignore_errors= True )
#    
 
if __name__ == '__main__':
    unittest.main()
