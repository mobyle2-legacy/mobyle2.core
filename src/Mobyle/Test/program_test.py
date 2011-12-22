import sys
sys.path.append( '/home/bneron/Mobyle/trunk/mobyle/')
sys.path.append( '/home/bneron/Mobyle/trunk/mobyle/Src')
from Mobyle import Parser2
p = Parser2.ServiceParser()
s = p.parse( "/home/bneron/Mobyle/trunk/mobyle/Src/Mobyle/Test/program.xml" )


