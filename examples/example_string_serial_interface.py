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
# region same code as other examples
from examples_settings import Settings  # do 1st to fix path if no pip install
settings = Settings()

if __name__ == "__main__":
    settings.load_cli_args(docstring=__doc__)
# endregion same code as other examples

from openlcb.canbus.seriallink import SerialLink

# specify connection information
# region replaced by settings
# device = "/dev/cu.usbmodemCC570001B1"
# endregion replaced by settings


s = SerialLink()
s.connect(settings['device'])

#######################

# send a AME frame in GridConnect string format with arbitrary source alias to
# elicit response
AME = ":X10702001N;"
s.send(AME)
print("SR: {}".format(AME.strip()))

# display response - should be RID from node(s)
while True:  # have to kill this manually
    print("RR: {}".format(s.receive().strip()))
