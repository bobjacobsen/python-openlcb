'''
Initial configuration for a compatibility check.

This runs at the start of each check to 
load configuration values into the "default"
space.  E.g. 'default.portname' will give
the portname being used now.

The sequence of operations is:
    read from the `defaults.py` file
    read from the `localoverrides.py` file
    process the command line arguments

'''

import os

def options() :
    print ("")
    #   TODO finish this up
    print ("Available options are:")
    print ("")
    print ("-h, --help print this message")
    print ("")
    print ("-a, --address followed by a host[:port] IP address for GridConnect access.")
    print ("                This is mutually exclusive with the -d --device option")
    print ("-d, --device followed by a serial port device name.")
    print ("                This is mutually exclusive with the -h --hostname option")
    print ("-t, --targetnode followed by a nodeID for the device being checked in 01.23.45.67.89.0A form")
    print ("")
    print ("Less frequently needed:")
    print ("")
    print ("-T, --trace followed by an integer trace level.  Higher numbers are more informatiom.")
    print ("                0 is just error messages, 10 includes success messages, 20 includes message traces, ")
    print ("                30 includes frame traces, 40 includes physical layer traces, 50 includes internal code traces")
    print ("-o, --ownnode followed by a nodeID for the checking device in 01.23.45.67.89.0A form")
    print ("-p do not check results against PIP bits")
    print ("-P do check results against PIP bits")
    print ("")

# First get the defaults.py file,
try:
    import defaults
except:
    print ("defaults.py not found, ending")
    quit(3)

#   TODO: Make the following into a loop over dir(defaults)
hostname = defaults.hostname
portnumber = defaults.portnumber
devicename = defaults.devicename
targetnodeid = defaults.targetnodeid
ownnodeid = defaults.ownnodeid
checkpip = defaults.checkpip
trace = defaults.trace

# Next override with local definitions.
if os.path.isfile("./localoverrides.py") :
    try:
        import localoverrides
        
        #   TODO: Make the following into a loop over dir(localoverrides)
        if 'hostname' in dir(localoverrides) :      hostname = localoverrides.hostname
        if 'portnumber' in dir(localoverrides) :    portnumber = localoverrides.portnumber
        if 'devicename' in dir(localoverrides) :    devicename = localoverrides.devicename
        if 'targetnodeid' in dir(localoverrides) :  targetnodeid = localoverrides.targetnodeid
        if 'ownnodeid' in dir(localoverrides) :     ownnodeid = localoverrides.ownnodeid
        if 'checkpip' in dir(localoverrides) :      checkpip = localoverrides.checkpip
        if 'trace' in dir(localoverrides) :         trace = localoverrides.trace

    except:
        pass  # no local overrides is a normal condition

# Next process command line options

import getopt, sys

try:
    opts, remainder = getopt.getopt(sys.argv[1:], "d:n:o:t:T:a:pPh", ["host=", "device=", "ownnode=", "targetnode=", "trace=", "help"])
except getopt.GetoptError as err:
    # print help information and exit:
    print (str(err)) # will print something like "option -a not recognized"
    options()
    sys.exit(2)
for opt, arg in opts:
    if opt in ("-h", "--help"):
        options()
        sys.exit(0)
    elif opt == "-p":
        checkpip = False
    elif opt == "-P":
        checkpip = True
    elif opt in ("-t", "--targetnode"):
        targetnodeid = arg
    elif opt in ("-d", "--device"):
        hostname = None # only one
        devicename = arg
    elif opt in ("-o", "--ownnode"):
        ownnodeid = arg
    elif opt in ("-T", "--trace"):
        trace = int(arg)
    elif opt in ("-a", "--address"):
        devicename = None # only one
        hostname = arg
        parts = arg.split(":")
        if len(parts) == 2:
            hostname = parts[0]
            try:
                portnumber = int(parts[1])
            except ValueError:
                usage()
                print("Error: Port {} is not an integer.".format(parts[1]),
                      file=sys.stderr)
                options()
                sys.exit(2)
        elif len(parts) > 2:
            print("Error: Too many colons in hostname argument",
                      file=sys.stderr)
            options()
            sys.exit(2)

# check that a connection has been configured
if (devicename is None and hostname is None ) or (devicename is not None and hostname is not None) :
    print ("Exactly one of host name and device name must be specified")
    options()
    sys.exit(2)
