'''
Demo of using the datagram service to send and receive a datagram

Usage:
python3 example_node_implementation.py [ip_address]

Options:
ip_address            (optional) defaults to a hard-coded test address
'''
from openlcb.tcpsocket import TcpSocket

from canbus.canphysicallayergridconnect import CanPhysicalLayerGridConnect
# from canbus.canframe import CanFrame
from canbus.canlink import CanLink
# from openlcb.controlframe import ControlFrame
from openlcb.nodeid import NodeID
from openlcb.datagramservice import (
    # DatagramWriteMemo,
    # DatagramReadMemo,
    DatagramService,
)
from openlcb.memoryservice import (
    # MemoryReadMemo,
    # MemoryWriteMemo,
    MemoryService,
)
from openlcb.localnodeprocessor import LocalNodeProcessor
from openlcb.pip import PIP
from openlcb.snip import SNIP
from openlcb.node import Node

# specify connection information
host = "192.168.16.212"
port = 12021
localNodeID = "05.01.01.01.03.01"
farNodeID = "09.00.99.03.00.35"

if __name__ == "__main__":
    # global host  # only necessary if this is moved to a main/other function
    import sys
    if len(sys.argv) > 1:
        host = sys.argv[1]

s = TcpSocket()
s.connect(host, port)

print("RR, SR are raw socket interface receive and send;"
      " RL, SL are link interface; RM, SM are message interface")


def sendToSocket(string):
    print("      SR: {}".format(string))
    s.send(string)


def printFrame(frame):
    print("   RL: {}".format(frame))


canPhysicalLayerGridConnect = CanPhysicalLayerGridConnect(sendToSocket)
canPhysicalLayerGridConnect.registerFrameReceivedListener(printFrame)


def printMessage(message):
    print("RM: {} from {}".format(message, message.source))


canLink = CanLink(NodeID(localNodeID))
canLink.linkPhysicalLayer(canPhysicalLayerGridConnect)
canLink.registerMessageReceivedListener(printMessage)

datagramService = DatagramService(canLink)
canLink.registerMessageReceivedListener(datagramService.process)


def printDatagram(memo):
    """create a call-back to print datagram contents when received

    Args:
        memo (_type_): _description_

    Returns:
        bool: Always False (True would mean we sent a reply to the datagram,
            but let the MemoryService do that).
    """
    print("Datagram receive call back: {}".format(memo.data))
    return False


datagramService.registerDatagramReceivedListener(printDatagram)

memoryService = MemoryService(datagramService)


# createcallbacks to get results of memory read
def memoryReadSuccess(memo):
    print("successful memory read: {}".format(memo.data))


def memoryReadFail(memo):
    print("memory read failed: {}".format(memo.data))


# create a node and connect it update
# This is a very minimal node, which just takes part in the low-level common
# protocols
localNode = Node(
    NodeID(localNodeID),
    SNIP("PythonOlcbNode", "example_node_implementation",
         "0.1", "0.2", "User Name Here", "User Description Here"),
    set([PIP.SIMPLE_NODE_IDENTIFICATION_PROTOCOL, PIP.DATAGRAM_PROTOCOL])
)

localNodeProcessor = LocalNodeProcessor(canLink, localNode)
canLink.registerMessageReceivedListener(localNodeProcessor.process)

#######################

# have the socket layer report up to bring the link layer up and get an alias
print("      SL : link up")
canPhysicalLayerGridConnect.physicalLayerUp()

# process resulting activity
while True:
    input = s.receive()
    print("      RR: "+input)
    # pass to link processor
    canPhysicalLayerGridConnect.receiveString(input)
