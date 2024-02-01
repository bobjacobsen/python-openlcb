'''
Demo of access to and from the message layer using a native TCP connection

This is an interface in terms of OpenLCB messages.

Usage:
python3 example_tcp_message_interface.py [host|host:port]

Options:
host|host:port            (optional) Set the address (or using a colon,
                          the address and port). Defaults to a hard-coded test
                          address and port.
'''
from tcplink.tcpsocket import TcpSocket
from tcplink.tcplink import TcpLink

from openlcb.nodeid import NodeID
from openlcb.message import Message
from openlcb.mti import MTI

# specify connection information
host = "192.168.16.212"
port = 12021
localNodeID = "05.01.01.01.03.01"

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

print("RR, SR are raw socket interface receive and send; "
      " RM, SM are message interface")


def sendToSocket(data):
    print("      SR: {}".format(data))
    s.send(data)

def printMessage(msg):
    print("RM: {} from {}".format(msg, msg.source))

tcpLinklayer = TcpLink(NodeID(100))
tcpLinklayer.registerMessageReceivedListener(printMessage)
tcpLinklayer.linkPhysicalLayer(sendToSocket)

#######################

# have the socket layer report up to bring the link layer up and get an alias
print("      SL : link up")
tcpLinklayer.linkUp()

# send an VerifyNodes message to provoke response
message = Message(MTI.Verify_NodeID_Number_Global, NodeID(localNodeID), None)
print("SM: {}".format(message))
tcpLinklayer.sendMessage(message)

# process resulting activity
while True:
    received = s.receive()
    print("      RR: {}".format(received))
    # pass to link processor
    tcpLinklayer.receiveListener(received)
