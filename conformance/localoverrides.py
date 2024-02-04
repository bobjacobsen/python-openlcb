# Exactly one of nostname or deviceanme must be provided here or in run-time options.
# hostname e.g. "localhost" or "192.168.21.3" specifies a GridConnect TCP connection
# devicename e.g. "/dev/cu-USBserial" specifies a serial port connection

hostname = "192.168.16.212"
targetnodeid = "09.00.99.03.00.35"

#devicename = "/dev/cu.usbmodemCC570001B1"
#targetnodeid = "02.01.57.00.04.58"

trace = 10
# higher numbers are more output:
#    0 only failures and errors
#   10 plus success info messages
#   20 plus message traces
#   30 plus frame level traces
#   40 plus serial level traces
#   50 plus internal code traces
