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
# region same code as other examples
from examples_settings import Settings  # do 1st to fix path if no pip install
settings = Settings()

if __name__ == "__main__":
    settings.load_cli_args(docstring=__doc__)
# endregion same code as other examples

from openlcb.tcplink.tcpsocket import TcpSocket
from openlcb.tcplink.tcplink import TcpLink

from openlcb.nodeid import NodeID
from openlcb.message import Message
from openlcb.mti import MTI

# specify connection information
# region moved to settings
# host = "localhost"
# port = 12022
# localNodeID = "05.01.01.01.03.01"
# endregion moved to settings

s = TcpSocket()
# s.settimeout(30)
print("Using settings:")
print(settings.dumps())
s.connect(settings['host'], settings['port'])

print("RR, SR are raw socket interface receive and send; "
      " RM, SM are message interface")


def sendToSocket(data):
    # if isinstance(data, list):
    #     raise TypeError(
    #         "Got {}({}) but expected str"
    #         .format(type(data).__name__, data)
    #     )
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
message = Message(MTI.Verify_NodeID_Number_Global,
                  NodeID(settings['localNodeID']), None)
print("SM: {}".format(message))
tcpLinklayer.sendMessage(message)

# process resulting activity
while True:
    received = s.receive()
    print("      RR: {}".format(received))
    # pass to link processor
    tcpLinklayer.receiveListener(received)
