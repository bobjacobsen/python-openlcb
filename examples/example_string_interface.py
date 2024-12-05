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

from openlcb.canbus.tcpsocket import TcpSocket

# specify connection information
# region replaced by settings
# host = "192.168.16.212"
# port = 12021
# endregion replaced by settings

# region same code as other examples
from examples_settings import Settings
settings = Settings()

if __name__ == "__main__":
    settings.load_cli_args(docstring=__doc__)
# endregion same code as other examples


s = TcpSocket()
# s.settimeout(30)
s.connect(settings['host'], settings['port'])

#######################

# send a AME frame in GridConnect string format with arbitrary source alias to
# elicit response
AME = ":X10702001N;"
s.send(AME)
print("SR: {}".format(AME.strip()))

# display response - should be RID from node(s)
while True:  # have to kill this manually
    print("RR: {}".format(s.receive().strip()))
