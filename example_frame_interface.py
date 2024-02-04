'''
Demo of access to and from the link layer.
This is an interface in terms of CAN frames.

Usage:
python3 example_frame_interface.py [host|host:port]

Options:
host|host:port            (optional) Set the address (or using a colon,
                          the address and port). Defaults to a hard-coded test
                          address and port.
'''

from openlcb.canbus.tcpsocket import TcpSocket
from openlcb.canbus.canphysicallayergridconnect import CanPhysicalLayerGridConnect
from openlcb.canbus.canframe import CanFrame
from openlcb.canbus.controlframe import ControlFrame

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
