'''
Demo of using the datagram service to send and receive a datagram

Usage:
python3 example_datagram_transfer.py [host|host:port]

Options:
host|host:port            (optional) Set the address (or using a colon,
                          the address and port). Defaults to a hard-coded test
                          address and port.
'''
# region same code as other examples
from examples_settings import Settings  # do 1st to fix path if no pip install
from openlcb import precise_sleep
settings = Settings()

if __name__ == "__main__":
    settings.load_cli_args(docstring=__doc__)
# endregion same code as other examples

import threading  # noqa:E402

from openlcb.tcplink.tcpsocket import TcpSocket  # noqa:E402
from openlcb.canbus.canphysicallayergridconnect import (  # noqa:E402
    CanPhysicalLayerGridConnect,
)
from openlcb.canbus.canlink import CanLink  # noqa:E402
from openlcb.nodeid import NodeID  # noqa:E402
from openlcb.datagramservice import (  # noqa:E402
    DatagramService,
    DatagramSendMemo,
)

# specify connection information
# region replaced by settings
# host = "192.168.16.212"
# port = 12021
# endregion replaced by settings

# localNodeID = "05.01.01.01.03.01"
# farNodeID = "09.00.99.03.00.35"
sock = TcpSocket()
# s.settimeout(30)
sock.connect(settings['host'], settings['port'])

print("RR, SR are raw socket interface receive and send;"
      " RL, SL are link interface; RM, SM are message interface")


# def sendToSocket(frame: CanFrame):
#     string = frame.encodeAsString()
#     print("      SR: "+string.strip())
#     sock.sendString(string)
#     physicalLayer.onFrameSent(frame)


def printFrame(frame):
    print("   RL: "+str(frame))


physicalLayer = CanPhysicalLayerGridConnect()
physicalLayer.registerFrameReceivedListener(printFrame)


def printMessage(message):
    print("RM: {} from {}".format(message, message.source))


canLink = CanLink(physicalLayer, NodeID(settings['localNodeID']))
canLink.registerMessageReceivedListener(printMessage)

datagramService = DatagramService(canLink)
canLink.registerMessageReceivedListener(datagramService.process)


# create a call-back for replies to write datagram
def sendCallBackCheck(memo):
    print("Write complete call back")


def datagramReceiver(memo):
    """A call-back for when datagrams received

    Args:
        DatagramReceiveMemo: The datagram object

    Returns:
        bool: Always True (means we sent the reply to this datagram)
    """
    print("Datagram receive call back: {}".format(memo.data))
    datagramService.positiveReplyToDatagram(memo)
    return True


datagramService.registerDatagramReceivedListener(datagramReceiver)

#######################

# have the socket layer report up to bring the link layer up and get an alias
print("      SL : link up...")
physicalLayer.physicalLayerUp()
print("      SL : link up...waiting...")
physicalLayer.physicalLayerUp()
print("      SL : link up")

while canLink.pollState() != CanLink.State.Permitted:
    physicalLayer.receiveAll(sock, verbose=settings['trace'])
    physicalLayer.sendAll(sock)
    precise_sleep(.02)


def datagramWrite():
    """Create and send a write datagram.
    This is a read of 20 bytes from the start of CDI space.
    We will fire it on a separate thread to give time for other nodes to reply
    to AME.
    """
    import time
    time.sleep(1)

    sendMemo = DatagramSendMemo(
        NodeID(settings['farNodeID']),
        bytearray([0x20, 0x43, 0x00, 0x00, 0x00, 0x00, 0x14]),
        sendCallBackCheck
    )
    datagramService.sendDatagram(sendMemo)


thread = threading.Thread(target=datagramWrite)
thread.start()

# process resulting activity
while True:
    count = 0
    count += physicalLayer.receiveAll(sock, verbose=settings['trace'])
    count += physicalLayer.sendAll(sock)
    if count < 1:
        precise_sleep(.01)
    # else skip sleep to avoid latency (port already delayed)

physicalLayer.physicalLayerDown()
