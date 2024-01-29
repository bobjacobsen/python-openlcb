# demo of access to and from the message layer, i.e. down through the link layer
# This is an interface in terms of OpenLCB messages.

# specify connection information
host = "192.168.16.212"
port = 12021
localNodeID = "05.01.01.01.03.01"

from tcpsocket import TcpSocket

s = TcpSocket()
s.connect(host, port)

from canphysicallayergridconnect import CanPhysicalLayerGridConnect
from canframe import CanFrame
from canlink import *
from controlframe import ControlFrame
from nodeid import *

print("RR, SR are raw socket interface receive and send; RL, SL are link interface; RM, SM are message interface")

def sendToSocket(string) :
    print("      SR: "+string)
    s.send(string)

def printFrame(frame) : 
    print("   RL: "+str(frame) )

canPhysicalLayerGridConnect = CanPhysicalLayerGridConnect(sendToSocket)
canPhysicalLayerGridConnect.registerFrameReceivedListener(printFrame)

def printMessage(msg) : 
    print("RM: "+str(msg)+" from "+str(msg.source))

canLink = CanLink(NodeID(localNodeID))
canLink.linkPhysicalLayer(canPhysicalLayerGridConnect)
canLink.registerMessageReceivedListener(printMessage)

#######################

# have the socket layer report up to bring the link layer up and get an alias
print("      SL : link up")
canPhysicalLayerGridConnect.physicalLayerUp()

# send an VerifyNodes message to provoke response
message = Message(MTI.Verify_NodeID_Number_Global, NodeID(localNodeID), None)
print("SM: "+str(message))
canLink.sendMessage(message)

# process resulting activity
while True:
    input = s.receive()
    print("      RR: "+input)
    # pass to link processor
    canPhysicalLayerGridConnect.receiveString(input)
