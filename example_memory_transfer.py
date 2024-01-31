'''
Demo of using the datagram service to send and receive a datagram

Usage:
python3 example_memory_transfer.py [host|host:port]

Options:
host|host:port            (optional) Set the address (or using a colon,
                          the address and port). Defaults to a hard-coded test
                          address and port.
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
    MemoryReadMemo,
    # MemoryWriteMemo,
    MemoryService,
)

# specify connection information
host = "192.168.16.212"
port = 12021
localNodeID = "05.01.01.01.03.01"
farNodeID = "09.00.99.03.00.35"

# region same code as other examples


def usage():
    print(__doc__, file=sys.stderr)


if __name__ == "__main__":
    # global host  # only necessary if this is moved to a main/other function
    import sys
    if len(sys.argv) == 2:
        host = sys.argv[1]
        parts = host.split(":")
        if len(parts) == 2:
            host = parts[0]
            try:
                port = int(parts[1])
            except ValueError:
                usage()
                print("Error: Port {} is not an integer.".format(parts[1]),
                      file=sys.stderr)
                sys.exit(1)
        elif len(parts) > 2:
            usage()
            print("Error: blank, address or address:port format was expected.")
            sys.exit(1)
    elif len(sys.argv) > 2:
        usage()
        print("Error: blank, address or address:port format was expected.")
        sys.exit(1)

# endregion same code as other examples

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
        bool: Always False (True would mean we sent a reply to this datagram,
            but let MemoryService do that).
    """
    print("Datagram receive call back: {}".format(memo.data))
    return False


datagramService.registerDatagramReceivedListener(printDatagram)

memoryService = MemoryService(datagramService)


def memoryReadSuccess(memo):
    """createcallbacks to get results of memory read

    Args:
        memo (_type_): _description_
    """
    print("successful memory read: {}".format(memo.data))


def memoryReadFail(memo):
    print("memory read failed: {}".format(memo.data))


#######################

# have the socket layer report up to bring the link layer up and get an alias
print("      SL : link up")
canPhysicalLayerGridConnect.physicalLayerUp()


def memoryRead():
    """Create and send a write datagram.
    This is a read of 20 bytes from the start of CDI space.
    We will fire it on a separate thread to give time for other nodes to reply
    to AME
    """
    import time
    time.sleep(1)

    # read 64 bytes from the CDI space starting at address zero
    memMemo = MemoryReadMemo(NodeID(farNodeID), 64, 0xFF, 0, memoryReadFail,
                             memoryReadSuccess)
    memoryService.requestMemoryRead(memMemo)


import threading  # noqa E402
thread = threading.Thread(target=memoryRead)
thread.start()

# process resulting activity
while True:
    received = s.receive()
    print("      RR: {}".format(received))
    # pass to link processor
    canPhysicalLayerGridConnect.receiveString(received)
