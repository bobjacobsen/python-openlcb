'''
Demo of using the datagram service to send and receive a datagram

Usage:
python3 example_node_implementation.py [host|host:port]

Options:
host|host:port            (optional) Set the address (or using a colon,
                          the address and port). Defaults to a hard-coded test
                          address and port.
'''
import socket

# region same code as other examples
from examples_settings import Settings  # do 1st to fix path if no pip install
settings = Settings()

if __name__ == "__main__":
    settings.load_cli_args(docstring=__doc__)
# endregion same code as other examples

from openlcb.canbus.tcpsocket import TcpSocket

from openlcb.canbus.canphysicallayergridconnect import (
    CanPhysicalLayerGridConnect,
)
from openlcb.canbus.canlink import CanLink
from openlcb.nodeid import NodeID
from openlcb.datagramservice import DatagramService
from openlcb.memoryservice import MemoryService
from openlcb.message import Message
from openlcb.mti import MTI

from openlcb.localnodeprocessor import LocalNodeProcessor
from openlcb.pip import PIP
from openlcb.snip import SNIP
from openlcb.node import Node

# specify connection information
# region moved to settings
# host = "192.168.16.212"
# port = 12021
# localNodeID = "05.01.01.01.03.01"
# farNodeID = "09.00.99.03.00.35"
# endregion moved to settings

s = TcpSocket()
# s.settimeout(30)
try:
    s.connect(settings['host'], settings['port'])
except socket.gaierror:
    print("Failure accessing {}:{}"
          .format(settings.get('host'), settings.get('port')))
    raise

print("RR, SR are raw socket interface receive and send;"
      " RL, SL are link interface; RM, SM are message interface")


def sendToSocket(string):
    print("      SR: {}".format(string.strip()))
    s.send(string)


def printFrame(frame):
    print("   RL: {}".format(frame))


canPhysicalLayerGridConnect = CanPhysicalLayerGridConnect(sendToSocket)
canPhysicalLayerGridConnect.registerFrameReceivedListener(printFrame)


def printMessage(message):
    print("RM: {} from {}".format(message, message.source))


canLink = CanLink(NodeID(settings['localNodeID']))
canLink.linkPhysicalLayer(canPhysicalLayerGridConnect)
canLink.registerMessageReceivedListener(printMessage)

datagramService = DatagramService(canLink)
canLink.registerMessageReceivedListener(datagramService.process)


def printDatagram(memo):
    """create a call-back to print datagram contents when received

    Args:
        memo (DatagramReadMemo): The datagram received

    Returns:
        bool: Always False (True would mean we sent a reply to the datagram,
            but let the MemoryService do that).
    """
    print("Datagram receive call back: {}".format(memo.data))
    return False


datagramService.registerDatagramReceivedListener(printDatagram)

memoryService = MemoryService(datagramService)


# callbacks to get results of memory read

def memoryReadSuccess(memo):
    print("successful memory read: {}".format(memo.data))


def memoryReadFail(memo):
    print("memory read failed: {}".format(memo.data))


# create a node and connect it update
# This is a very minimal node, which just takes part in the low-level common
# protocols
localNode = Node(
    NodeID(settings['localNodeID']),
    SNIP("python-openlcb", "example_node_implementation",
         "0.1", "0.2", "User Name Here", "User Description Here"),
    set([PIP.SIMPLE_NODE_IDENTIFICATION_PROTOCOL, PIP.DATAGRAM_PROTOCOL])
)

localNodeProcessor = LocalNodeProcessor(canLink, localNode)
canLink.registerMessageReceivedListener(localNodeProcessor.process)


def displayOtherNodeIds(message) :
    """Listener to identify connected nodes

    Args:
        message (Message): A response from the network
    """
    print("[displayOtherNodeIds] type(message): {}"
          "".format(type(message).__name__))
    if message.mti == MTI.Verified_NodeID :
        print("Detected farNodeID is {}".format(message.source))


canLink.registerMessageReceivedListener(displayOtherNodeIds)


#######################

# have the socket layer report up to bring the link layer up and get an alias
print("      SL : link up")
canPhysicalLayerGridConnect.physicalLayerUp()

# request that nodes identify themselves so that we can print their node IDs
message = Message(MTI.Verify_NodeID_Number_Global,
                  NodeID(settings['localNodeID']), None)
canLink.sendMessage(message)

# process resulting activity
while True:
    input = s.receive()
    print("      RR: "+input.strip())
    # pass to link processor
    canPhysicalLayerGridConnect.receiveString(input)
