# Demo of using the datagram service to send and receive a datagram

# specify connection information
host = "192.168.16.212"
port = 12021
localNodeID = "05.01.01.01.03.01"
farNodeID   = "09.00.99.03.00.35"

from openlcb.tcpsocket import TcpSocket
s = TcpSocket()
s.connect(host, port)

from canbus.canphysicallayergridconnect import CanPhysicalLayerGridConnect
# from canbus.canframe import CanFrame
from canbus.canlink import CanLink
# from openlcb.controlframe import ControlFrame
from openlcb.nodeid import NodeID
from openlcb.datagramservice import (
    DatagramService,
    DatagramWriteMemo,
)

print("RR, SR are raw socket interface receive and send; RL, SL are link interface; RM, SM are message interface")


def sendToSocket(string) :
    print("      SR: "+string)
    s.send(string)


def printFrame(frame) :
    print("   RL: "+str(frame) )


canPhysicalLayerGridConnect = CanPhysicalLayerGridConnect(sendToSocket)
canPhysicalLayerGridConnect.registerFrameReceivedListener(printFrame)


def printMessage(message) :
    print("RM: "+str(message)+" from "+str(message.source))


canLink = CanLink(NodeID(localNodeID))
canLink.linkPhysicalLayer(canPhysicalLayerGridConnect)
canLink.registerMessageReceivedListener(printMessage)

datagramService = DatagramService(canLink)
canLink.registerMessageReceivedListener(datagramService.process)


# create a call-back for replies to write datagram
def writeCallBackCheck(memo) :
    print("Write complete call back")


# create a call-back for when datagrams received
def datagramReceiver(memo):
    print("Datagram receive call back: "+str(memo.data))
    datagramService.positiveReplyToDatagram(memo)
    return True # means we sent the reply to this datagram
datagramService.registerDatagramReceivedListener(datagramReceiver)

#######################

# have the socket layer report up to bring the link layer up and get an alias
print("      SL : link up")
canPhysicalLayerGridConnect.physicalLayerUp()


def datagramWrite():
    """Create and send a write datagram.
    This is a read of 20 bytes from the start of CDI space.
    We will fire it on a separate thread to give time for other nodes to reply to AME.
    """
    import time
    time.sleep(1)

    writeMemo = DatagramWriteMemo(NodeID(farNodeID), [0x20, 0x43, 0x00, 0x00, 0x00, 0x00, 0x14], writeCallBackCheck)
    datagramService.sendDatagram(writeMemo)


import threading
thread = threading.Thread(target=datagramWrite)
thread.start()

# process resulting activity
while True:
    input = s.receive()
    print("      RR: "+input)
    # pass to link processor
    canPhysicalLayerGridConnect.receiveString(input)
