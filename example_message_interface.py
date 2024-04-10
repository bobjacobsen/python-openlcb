'''
Demo of access to and from the message layer, i.e. down through the link layer

This is an interface in terms of OpenLCB messages.

Usage:
python3 example_message_interface.py [host|host:port]

Options:
host|host:port            (optional) Set the address (or using a colon,
                          the address and port). Defaults to a hard-coded test
                          address and port.
'''
from openlcb.canbus.tcpsocket import TcpSocket

from openlcb.canbus.canphysicallayergridconnect import (
    CanPhysicalLayerGridConnect,
)
from openlcb.canbus.canlink import CanLink
from openlcb.nodeid import NodeID
from openlcb.message import Message
from openlcb.mti import MTI

# specify connection information
# region replaced by settings
# host = "192.168.16.212"
# port = 12021
# localNodeID = "05.01.01.01.03.01"
# endregion replaced by settings

# region same code as other examples
from examples_settings import Settings
settings = Settings()

if __name__ == "__main__":
    settings.load_cli_args(docstring=__doc__)
# endregion same code as other examples

s = TcpSocket()
s.connect(settings['host'], settings['port'])

print("RR, SR are raw socket interface receive and send; RL,"
      " SL are link interface; RM, SM are message interface")


def sendToSocket(string):
    print("      SR: {}".format(string.strip()))
    s.send(string)


def printFrame(frame):
    print("   RL: {}".format(frame))


canPhysicalLayerGridConnect = CanPhysicalLayerGridConnect(sendToSocket)
canPhysicalLayerGridConnect.registerFrameReceivedListener(printFrame)


def printMessage(msg):
    print("RM: {} from {}".format(msg, msg.source))


canLink = CanLink(NodeID(settings['localNodeID']))
canLink.linkPhysicalLayer(canPhysicalLayerGridConnect)
canLink.registerMessageReceivedListener(printMessage)

#######################

# have the socket layer report up to bring the link layer up and get an alias
print("      SL : link up")
canPhysicalLayerGridConnect.physicalLayerUp()

# send an VerifyNodes message to provoke response
message = Message(MTI.Verify_NodeID_Number_Global,
                  NodeID(settings['localNodeID']), None)
print("SM: {}".format(message))
canLink.sendMessage(message)

# process resulting activity
while True:
    received = s.receive()
    print("      RR: {}".format(received.strip()))
    # pass to link processor
    canPhysicalLayerGridConnect.receiveString(received)
