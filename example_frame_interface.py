'''
Demo of access to and from the link layer.
This is an interface in terms of CAN frames.

Usage:
python3 example_frame_interface.py [ip_address]

Options:
ip_address            (optional) defaults to a hard-coded test address
'''

from openlcb.tcpsocket import TcpSocket
from canbus.canphysicallayergridconnect import CanPhysicalLayerGridConnect
from canbus.canframe import CanFrame
from openlcb.controlframe import ControlFrame

# specify connection information
host = "192.168.16.212"
port = 12021

if __name__ == "__main__":
    # global host  # only necessary if this is moved to a main/other function
    import sys
    if len(sys.argv) > 1:
        host = sys.argv[1]

s = TcpSocket()
s.connect(host, port)

print("RR, SR are raw socket interface receive and send;"
      " RL, SL are link (frame) interface")


def sendToSocket(string):
    print("   SR: {}".format(string))
    s.send(string)


def printFrame(frame):
    print("RL: {}".format(frame))


canPhysicalLayerGridConnect = CanPhysicalLayerGridConnect(sendToSocket)
canPhysicalLayerGridConnect.registerFrameReceivedListener(printFrame)

# send an AME frame with arbitrary alias to provoke response
frame = CanFrame(ControlFrame.AME.value, 1, [])
print("SL: {}".format(frame))
canPhysicalLayerGridConnect.sendCanFrame(frame)

# display response - should be RID from nodes
while True:
    received = s.receive()
    print("   RR: {}".format(received))
    # pass to link processor
    canPhysicalLayerGridConnect.receiveString(received)
