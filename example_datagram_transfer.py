'''
Demo of using the datagram service to send and receive a datagram

Usage:
python3 example_datagram_transfer.py [host|host:port]

Options:
host|host:port            (optional) Set the address (or using a colon,
                          the address and port). Defaults to a hard-coded test
                          address and port.
'''
import threading

from openlcb.canbus.tcpsocket import TcpSocket
from openlcb.canbus.canphysicallayergridconnect import CanPhysicalLayerGridConnect
from openlcb.canbus.canlink import CanLink
from openlcb.nodeid import NodeID
from openlcb.datagramservice import (
    DatagramService,
    DatagramWriteMemo,
)

# specify connection information
host = "192.168.16.212"
port = 12021

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


localNodeID = "05.01.01.01.03.01"
farNodeID = "09.00.99.03.00.35"
s = TcpSocket()
s.connect(host, port)

print("RR, SR are raw socket interface receive and send;"
      " RL, SL are link interface; RM, SM are message interface")


def sendToSocket(string):
    print("      SR: "+string.strip())
    s.send(string)


def printFrame(frame):
    print("   RL: "+str(frame))


canPhysicalLayerGridConnect = CanPhysicalLayerGridConnect(sendToSocket)
canPhysicalLayerGridConnect.registerFrameReceivedListener(printFrame)


def printMessage(message):
    print("RM: {} from {}".format(message, message.source))


canLink = CanLink(NodeID(localNodeID))
canLink.linkPhysicalLayer(canPhysicalLayerGridConnect)
canLink.registerMessageReceivedListener(printMessage)

datagramService = DatagramService(canLink)
canLink.registerMessageReceivedListener(datagramService.process)


# create a call-back for replies to write datagram
def writeCallBackCheck(memo):
    print("Write complete call back")


def datagramReceiver(memo):
    """A call-back for when datagrams received

    Args:
        _type_: _description_

    Returns:
        bool: Always True (means we sent the reply to this datagram)
    """
    print("Datagram receive call back: {}".format(memo.data))
    datagramService.positiveReplyToDatagram(memo)
    return True


datagramService.registerDatagramReceivedListener(datagramReceiver)

#######################

# have the socket layer report up to bring the link layer up and get an alias
print("      SL : link up")
canPhysicalLayerGridConnect.physicalLayerUp()


def datagramWrite():
    """Create and send a write datagram.
    This is a read of 20 bytes from the start of CDI space.
    We will fire it on a separate thread to give time for other nodes to reply
    to AME.
    """
    import time
    time.sleep(1)

    writeMemo = DatagramWriteMemo(
        NodeID(farNodeID),
        [0x20, 0x43, 0x00, 0x00, 0x00, 0x00, 0x14],
        writeCallBackCheck
    )
    datagramService.sendDatagram(writeMemo)


thread = threading.Thread(target=datagramWrite)
thread.start()

# process resulting activity
while True:
    received = s.receive()
    print("      RR: {}".format(received.strip()))
    # pass to link processor
    canPhysicalLayerGridConnect.receiveString(received)
