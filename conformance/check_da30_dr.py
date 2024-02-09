#!/usr/bin/env python3.10
'''
This uses a CAN link layer to check Datagram exchange.

Usage:
python3.10 check_da30_dr.py

The -h option will display a full list of options.
'''

import sys

from openlcb.nodeid import NodeID
from openlcb.message import Message
from openlcb.mti import MTI
from openlcb.pip import PIP

from queue import Empty

def check():
    # set up the infrastructure

    import conformance.setup
    trace = conformance.trace() # just to be shorter

    # pull any early received messages
    conformance.purgeMessages()

    # get configured DUT node ID - this uses Verify Global in some cases, but not all
    destination = conformance.getTargetID()

    ###############################
    # checking sequence starts here
    ###############################
    
    # check if PIP says this is present
    if conformance.isCheckPip() : 
        pipSet = conformance.gatherPIP(destination)
        if pipSet is None:
            print ("Failed in setup, no PIP information received")
            return (2)
        if not PIP.DATAGRAM_PROTOCOL in pipSet :
            if trace >= 10 : 
                print("Passed - due to Datagram protocol not in PIP")
            return(0)

    sampleLengths = [ 1, 10, 72]
    
    for length in sampleLengths:

        data = list(range(0, length))

        # send an datagram to provoke response
        message = Message(MTI.Datagram, NodeID(conformance.ownnodeid()), destination, data)
        conformance.sendMessage(message)

        while True :
            try :
                received = conformance.getMessage() # timeout if no entries
                # is this a datagram reply, OK or not?
                if not (received.mti == MTI.Datagram_Received_OK or received.mti == MTI.Datagram_Rejected) : 
                    continue # wait for next
        
                if destination != received.source : # check source in message header
                    print ("Failure - Unexpected source of reply message: {} {}".format(received, received.source))
                    return(3)
        
                if NodeID(conformance.ownnodeid()) != received.destination : # check destination in message header
                    print ("Failure - Unexpected destination of reply message: {} {}".format(received, received.destination))
                    return(3)
        
                if received.mti == MTI.Datagram_Received_OK :
                    # check for exactly one byte of flags
                    if len(received.data) != 1 :
                        print ("Failure - Unexpected length in OK reply: {}".format(len(received.data)))
                        return(3)
                else : # must be datagram rejected
                    # check for contains at least 2 bytes of error code 
                    if len(received.data) != 2 :
                        print ("Failure - Unexpected length in reject reply: {}".format(len(received.data)))
                        return(3)
                    # check for valid flags
                    bits = received.data[0]
                    if (bits & 0xF0 ) != 0x10 and (bits & 0xF0 ) != 0x10 :
                        print ("Failure - Unexpected contents flag upper nibble contents: 0x{:02X}".format(received.data[0]))
                        return(3)
                    if (bits & 0x0F ) != 0x00:
                        print ("Failure - Unexpected contents flag 2nd nibble contents: 0x{:02X}".format(received.data[0]))
                        return(3)
                break
            except Empty:
                print ("Failure - no reply to PIP request")
                return(3)

    if trace >= 10 : print("Passed")
    return 0

if __name__ == "__main__":
    sys.exit(check())
