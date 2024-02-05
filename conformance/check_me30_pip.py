#!/usr/bin/env python3.10
'''
This uses a CAN link layer to test PIP message exchange.

Usage:
python3.10 check_me30_pip.py

The -h option will display a full list of options.
'''

import sys

from openlcb.nodeid import NodeID
from openlcb.message import Message
from openlcb.mti import MTI
from openlcb.pip import PIP

from queue import Empty

def test():
    # set up the infrastructure

    import conformance.setup
    trace = conformance.trace() # just to be shorter
    timeout = 0.8

    # pull any early received messages
    conformance.purgeMessages()

    # get configured DUT node ID - this uses Verify Global in some cases, but not all
    destination = conformance.getTargetID(timeout)

    ###########################
    # test sequence starts here
    ###########################
    
    # send an PIP message to provoke response
    message = Message(MTI.Protocol_Support_Inquiry, NodeID(conformance.ownnodeid()), destination)
    conformance.sendMessage(message)

    while True :
        try :
            received = conformance.getMessage(timeout) # timeout if no entries
            # is this a pip reply?
            if not received.mti == MTI.Protocol_Support_Reply : continue # wait for next
        
            if destination != received.source : # check source in message header
                print ("Failure - Unexpected source of reply message: {} {}".format(received, received.source))
                return(3)
        
            if NodeID(conformance.ownnodeid()) != received.destination : # check destination in message header
                print ("Failure - Unexpected destination of reply message: {} {}".format(received, received.destination))
                return(3)
        
            result = received.data[0] << 24 | \
                        received.data[1] << 16 | \
                        received.data[2] <<8|  \
                        received.data[3]
            if trace >= 10 :
                print("PIP reports:")
                list = PIP.contentsNamesFromInt(result)
                for e in list :
                    print (" ",e)
            if received.data[3] != 0 :
                print ("Failure - Unexpected contents in 4th byte; 0x{:02X}".format(received.data[3]))
                return(3)
            break
        except Empty:
            print ("Failure - no reply to PIP request")
            return(3)

    if trace >= 10 : print("Passed")
    return 0

if __name__ == "__main__":
    sys.exit(test())
