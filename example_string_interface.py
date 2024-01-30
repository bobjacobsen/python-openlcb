'''
Example of raw socket communications over the physical connection, in this case
a socket.

Usage:
python3 example_string_interface.py [ip_address]

Options:
ip_address            (optional) defaults to a hard-coded test address
'''

from openlcb.tcpsocket import TcpSocket

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

#######################

# send a AME frame in GridConnect string format with arbitrary source alias to
# elicit response
AME = ":X10702001N;"
s.send(AME)
print("SR: {}".format(AME))

# display response - should be RID from node(s)
while True:  # have to kill this manually
    print("RR: {}".format(s.receive()))
