'''
Example of raw socket communications over the physical connection, in this case
a socket.

Usage:
python3 example_string_interface.py [host|host:port]

Options:
host|host:port            (optional) Set the address (or using a colon,
                          the address and port). Defaults to a hard-coded test
                          address and port.
'''

from canbus.tcpsocket import TcpSocket

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

#######################

# send a AME frame in GridConnect string format with arbitrary source alias to
# elicit response
AME = ":X10702001N;"
s.send(AME)
print("SR: {}".format(AME))

# display response - should be RID from node(s)
while True:  # have to kill this manually
    print("RR: {}".format(s.receive()))
