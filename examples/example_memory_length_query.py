'''
Demo of using the memory service to get the length of a node memory

Usage:
python3 example_memory_transfer.py [host|host:port]

Options:
host|host:port            (optional) Set the address (or using a colon,
                          the address and port). Defaults to a hard-coded test
                          address and port.
'''
# region same code as other examples
from examples_settings import Settings  # do 1st to fix path if no pip install
settings = Settings()

if __name__ == "__main__":
    settings.load_cli_args(docstring=__doc__)
# endregion same code as other examples

from openlcb import precise_sleep  # noqa: E402
from openlcb.tcplink.tcpsocket import TcpSocket  # noqa: E402

from openlcb.canbus.canphysicallayergridconnect import (  # noqa: E402
    CanPhysicalLayerGridConnect,
)
from openlcb.canbus.canlink import CanLink  # noqa: E402
from openlcb.nodeid import NodeID  # noqa: E402
from openlcb.datagramservice import (  # noqa: E402
    # DatagramSendMemo,
    # DatagramReceiveMemo,
    DatagramService,
)
from openlcb.memoryservice import (  # noqa: E402
    # MemoryReadMemo,
    # MemoryWriteMemo,
    MemoryService,
)

# specify connection information
# region replaced by settings
host = "192.168.16.212"
port = 12021
localNodeID = "05.01.01.01.03.01"
farNodeID = "09.00.99.03.00.35"
# endregion replaced by settings

sock = TcpSocket()
# s.settimeout(30)
sock.connect(settings['host'], settings['port'])

print("RR, SR are raw socket interface receive and send;"
      " RL, SL are link interface; RM, SM are message interface")


# def sendToSocket(frame: CanFrame):
#     string = frame.encodeAsString()
#     print("      SR: {}".format(string.strip()))
#     sock.sendString(string)
#     physicalLayer.onFrameSent(frame)


def printFrame(frame):
    print("   RL: {}".format(frame))


physicalLayer = CanPhysicalLayerGridConnect()
physicalLayer.registerFrameReceivedListener(printFrame)


def printMessage(message):
    print("RM: {} from {}".format(message, message.source))


canLink = CanLink(physicalLayer, NodeID(settings['localNodeID']))
canLink.registerMessageReceivedListener(printMessage)

datagramService = DatagramService(canLink)
canLink.registerMessageReceivedListener(datagramService.process)


def printDatagram(memo):
    """create a call-back to print datagram contents when received

    Args:
        memo (DatagramReceiveMemo): The datagram received

    Returns:
        bool: Always False (True would mean we sent a reply to this datagram,
            but let MemoryService do that).
    """
    print("Datagram receive call back: {}".format(memo.data))
    return False


datagramService.registerDatagramReceivedListener(printDatagram)

memoryService = MemoryService(datagramService)

# callbacks to get results of memory read

# def memoryReadSuccess(memo):
#     """Handle a successful read
#
#     Args:
#         memo (MemoryReadMemo): Event that was generated.
#     """
#     print("successful memory read: {}".format(memo.data))
#
#
# def memoryReadFail(memo):
#     print("memory read failed: {}".format(memo.data))


def memoryLengthReply(address) :
    print("memory length reply: "+str(address))


#######################

# have the socket layer report up to bring the link layer up and get an alias

print("      SL : link up...")
physicalLayer.physicalLayerUp()
print("      SL : link up...waiting...")
physicalLayer.physicalLayerUp()


while canLink.pollState() != CanLink.State.Permitted:
    physicalLayer.receiveAll(sock, verbose=settings['trace'])
    physicalLayer.sendAll(sock, verbose=True)
    precise_sleep(.02)
print("      SL : link up")


def memoryRequest():
    """Create and send a read datagram.
    This is a read of 20 bytes from the start of CDI space.
    We will fire it on a separate thread to give time for other nodes to reply
    to AME
    """
    import time
    time.sleep(1)

    # request the length of the CDI space
#     memMemo = MemoryReadMemo(NodeID(settings['farNodeID']),
#                              64, 0xFF, 0, memoryReadFail,
#                              memoryReadSuccess)
    memoryService.requestSpaceLength(0xFF, NodeID(settings['farNodeID']),
                                     memoryLengthReply)


import threading  # noqa E402
thread = threading.Thread(target=memoryRequest)
thread.start()

# process resulting activity
while True:
    count = 0
    count += physicalLayer.receiveAll(sock, verbose=settings['trace'])
    count += physicalLayer.sendAll(sock, verbose=True)
    if count < 1:
        precise_sleep(.01)
    # else skip sleep to avoid latency (port already delayed)

physicalLayer.physicalLayerDown()
