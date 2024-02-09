# Exactly one of hostname or deviceanme must be provided.
# hostname e.g. "localhost" or "192.168.21.3" specifies a GridConnect TCP connection
# devicename e.g. "/dev/cu-USBserial" specifies a serial port connection

hostname = None
portnumber = 12021

devicename = None

targetnodeid = None
# None means to query for it, assuming only one present

ownnodeid = "03.00.00.00.00.01"
# taken from NMRA user zero, for now

checkpip = True
# True means checks are not run and are marked passed if PIP does not include the Standard being checked.
# False means the checks are run regardless of whether the protocol is included in PIP or not

trace = 10
# higher numbers are more output:
#    0 only failures and errors
#   10 plus success info messages
#   20 plus message traces
#   30 plus frame level traces
#   40 plus serial level traces
#   50 plus internal code traces
