# demo of access to and from the link layer.
# This is an interface in terms of CAN frames.

# specify connection information
host = "192.168.16.212"
port = 12021

from openlcb.tcpsocket import TcpSocket

s = TcpSocket()
s.connect(host, port)

from canbus.canphysicallayergridconnect import CanPhysicalLayerGridConnect
from canbus.canframe import CanFrame
from controlframe import ControlFrame

print("RR, SR are raw socket interface receive and send; RL, SL are link (frame) interface")


def sendToSocket(string):
    print("   SR: "+string)
    s.send(string)


def printFrame(frame):
    print("RL: "+str(frame))


canPhysicalLayerGridConnect = CanPhysicalLayerGridConnect(sendToSocket)
canPhysicalLayerGridConnect.registerFrameReceivedListener(printFrame)

# send an AME frame with arbitrary alias to provoke response
frame = CanFrame(ControlFrame.AME.value, 1, [])
print("SL: "+str(frame))
canPhysicalLayerGridConnect.sendCanFrame(frame)

# display response - should be RID from nodes
while True:
    input = s.receive()
    print("   RR: "+input)
    # pass to link processor
    canPhysicalLayerGridConnect.receiveString(input)