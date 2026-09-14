'''
Demo of creating a virtual node to represent the application
(other local nodes are possible, but at least one is necessary
for the application to announce itself and provide SNIP info).

Usage:
python3 example_node_implementation.py [host|host:port]

Options:
host|host:port            (optional) Set the address (or using a colon,
                          the address and port). Defaults to a hard-coded test
                          address and port.
'''
import os
import socket
from typing import Set, Union

# region same code as other examples
from examples_settings import Settings
from openlcb.convert import Convert
settings = Settings()

if __name__ == "__main__":
    settings.load_cli_args(docstring=__doc__)
# endregion same code as other examples

from openlcb import prDim, precise_sleep  # noqa: E402
from openlcb.tcplink.tcpsocket import TcpSocket  # noqa: E402

from openlcb.canbus.canphysicallayergridconnect import (  # noqa: E402
    CanPhysicalLayerGridConnect,
)
from openlcb.canbus.canlink import CanLink  # noqa: E402
from openlcb.nodeid import NodeID  # noqa: E402
from openlcb.datagramservice import DatagramService  # noqa: E402
from openlcb.memoryservice import MemoryService  # noqa: E402
from openlcb.message import Message  # noqa: E402
from openlcb.mti import MTI  # noqa: E402

from openlcb.localnodeprocessor import LocalNodeProcessor  # noqa: E402
from openlcb.pip import PIP  # noqa: E402
from openlcb.snip import SNIP  # noqa: E402
from openlcb.node import Node  # noqa: E402

# specify connection information
# region moved to settings
# host = "192.168.16.212"
# port = 12021
# localNodeID = "05.01.01.01.03.01"
# farNodeID = "09.00.99.03.00.35"
# endregion moved to settings

sock = TcpSocket()
# s.settimeout(30)
try:
    sock.connect(settings['host'], settings['port'])
except socket.gaierror:
    print("Failure accessing {}:{}"
          .format(settings.get('host'), settings.get('port')))
    raise

print("RR, SR are raw socket interface receive and send;"
      " RL, SL are link interface; RM, SM are message interface")


# def sendToSocket(frame: CanFrame):
#     string = frame.encodeAsString()
#     print("      SR: {}".format(string.strip()))
#     sock.sendString(string)
#     physicalLayer.onFrameSent(frame)

me = os.path.basename(__file__)


def printFrame(frame):
    prDim("   RL: {}".format(frame))


physicalLayer = CanPhysicalLayerGridConnect()
physicalLayer.registerFrameReceivedListener(printFrame)


def printMessage(message: Message):
    """Received message (RM) handler."""
    prDim(f"RM: {message.mti} from {message.source}")


localNodeID = NodeID(settings['localNodeID'])
print()
print(f"[example_node_memory_implementation] localNodeID: {localNodeID}")

canLink = CanLink(physicalLayer, localNodeID)
datagramService = DatagramService(canLink)
canLink.registerMessageReceivedListener(datagramService.process)
canLink.registerMessageReceivedListener(printMessage)


def printDatagram(memo):
    """create a call-back to print datagram contents when received

    Args:
        memo (DatagramReceiveMemo): The datagram received

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
    localNodeID,
    snip=SNIP("python-openlcb", "example_node_implementation",
              "0.1", "0.2", "Example Node Implementation",
              "Example from python-openlcb"),
    pipSet=set([
        PIP.SIMPLE_NODE_IDENTIFICATION_PROTOCOL,
        PIP.DATAGRAM_PROTOCOL,
    ])
)

localNodeProcessor = LocalNodeProcessor(canLink, localNode)
canLink.registerMessageReceivedListener(localNodeProcessor.process)
# ^ Must be registered after CanPhysicalLayer constructor
#   since that registers canLink.handleFrameReceived which
#   maps aliases and allows us to reply if request was the
#   first message to supply the far NodeID.


def displayOtherNodeIds(message: Message) :
    """Listener to identify connected nodes

    Args:
        message (Message): A response from the network
    """
    if message.mti == MTI.Verified_NodeID :
        print(f"[displayOtherNodeIds] Detected farNodeID {message.source}")
    else:
        print(f"[displayOtherNodeIds] {message.mti} from {message.source}")


canLink.registerMessageReceivedListener(displayOtherNodeIds)


#######################

# have the socket layer report up to bring the link layer up and get an alias

print("      SL : link up...")
physicalLayer.physicalLayerUp()
print("      SL : link up...waiting...")
while canLink.pollState() != CanLink.State.Permitted:
    physicalLayer.receiveAll(sock, verbose=settings['trace'],
                             verbose_fn=prDim)
    physicalLayer.sendAll(sock, verbose=True,
                          verbose_fn=prDim)
    precise_sleep(.02)
print("      SL : link up")
# request that nodes identify themselves so that we can print their node IDs
message = Message(MTI.Verify_NodeID_Number_Global,
                  localNodeID, None)
canLink.sendMessage(message)

# process resulting activity
while True:
    count = 0
    try:
        count += physicalLayer.sendAll(sock, verbose=True,
                                       verbose_fn=prDim)
        count += physicalLayer.receiveAll(sock, verbose=settings['trace'],
                                          verbose_fn=prDim)
        if count < 1:
            precise_sleep(.01)
        # else skip sleep to avoid latency (port already delayed)
    except Exception:
        print(f"localNodeID={localNodeID}")
        raise

print("Calling physicalLayerDown...")
physicalLayer.physicalLayerDown()
