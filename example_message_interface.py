'''
demo of access to and from the message layer, i.e. down through the link layer

This is an interface in terms of OpenLCB messages.

Usage:
python3 example_message_interface.py [ip_address]

Options:
ip_address            (optional) defaults to a hard-coded test address
'''
from openlcb.tcpsocket import TcpSocket

from canbus.canphysicallayergridconnect import CanPhysicalLayerGridConnect
# from canbus.canframe import CanFrame
from canbus.canlink import CanLink
# from openlcb.controlframe import ControlFrame
from openlcb.nodeid import NodeID
from openlcb.message import Message
from openlcb.mti import MTI

# specify connection information
host = "192.168.16.212"
port = 12021
localNodeID = "05.01.01.01.03.01"

if __name__ == "__main__":
    # global host  # only necessary if this is moved to a main/other function
    import sys
    if len(sys.argv) > 1:
        host = sys.argv[1]

s = TcpSocket()
s.connect(host, port)

print("RR, SR are raw socket interface receive and send; RL,"
      " SL are link interface; RM, SM are message interface")


def sendToSocket(string):
    print("      SR: {}".format(string))
    s.send(string)


def printFrame(frame):
    print("   RL: {}".format(frame))


canPhysicalLayerGridConnect = CanPhysicalLayerGridConnect(sendToSocket)
canPhysicalLayerGridConnect.registerFrameReceivedListener(printFrame)


def printMessage(msg):
    print("RM: {} from {}".format(msg, msg.source))


canLink = CanLink(NodeID(localNodeID))
canLink.linkPhysicalLayer(canPhysicalLayerGridConnect)
canLink.registerMessageReceivedListener(printMessage)

#######################

# have the socket layer report up to bring the link layer up and get an alias
print("      SL : link up")
canPhysicalLayerGridConnect.physicalLayerUp()

# send an VerifyNodes message to provoke response
message = Message(MTI.Verify_NodeID_Number_Global, NodeID(localNodeID), None)
print("SM: {}".format(message))
canLink.sendMessage(message)

# process resulting activity
while True:
    received = s.receive()
    print("      RR: {}".format(received))
    # pass to link processor
    canPhysicalLayerGridConnect.receiveString(received)
