#!/usr/bin/env python3.10
'''
This uses a CAN link layer to check for an OIR reply to an unknown MTI

Usage:
python3.10 check_me40_oir.py

The -h option will display a full list of options.
'''

import sys

from openlcb.nodeid import NodeID
from openlcb.message import Message
from openlcb.mti import MTI

from queue import Empty

def check() :
    # set up the infrastructure

    import olcbchecker.setup
    trace = olcbchecker.trace() # just to be shorter

    # pull any early received messages
    olcbchecker.purgeMessages()

    # get configured DUT node ID - this uses Verify Global in some cases, but not all
    destination = olcbchecker.getTargetID()

    ###############################
    # checking sequence starts here
    ###############################
    
    # send a message with bogus MTI to provoke response
    message = Message(MTI.New_Node_Seen, NodeID(olcbchecker.ownnodeid()), destination) # MTI selected to be addressed
    olcbchecker.sendMessage(message)

    while True :
        try :
            received = olcbchecker.getMessage() # timeout if no entries
            # is this a reply from that node?
            if not received.mti == MTI.Optional_Interaction_Rejected : continue # wait for next
            # this is a OIR message, success

            if destination != received.source : # check source in message header
                print ("Failure - Unexpected source of reply message: {} {}".format(received, received.source))
                return(3)
        
            if NodeID(olcbchecker.ownnodeid()) != received.destination : # check destination in message header
                print ("Failure - Unexpected destination of reply message: {} {}".format(received, received.destination))
                return(3)
            if len(received.data) < 4:
                print ("Failure - Unexpected length of reply message: {} {}".format(received, received.data))
                return(3)

            try :            
                seenMTI = MTI(0x2000|received.data[2]<<8 | received.data[3])
            except ValueError :
                seenMTI = None
            if seenMTI != MTI.New_Node_Seen :
                print ("Failure - MTI not carried in data: {} {}".format(received, received.data, seenMTI))
                try :
                    earlyMTI = MTI(0x2000|received.data[0]<<8 | received.data[1])
                except ValueError:
                    earlyMTI = None
                if earlyMTI == MTI.New_Node_Seen :
                    print("    Hint: MTI incorrectly found in first two bytes of OIR reply")
                return(3)
            
            break
        except Empty:
            print ("Failure - Did not receive Optional Interaction Rejected reply")
            return(3)

    if trace >= 10 : print("Passed")
    return 0

if __name__ == "__main__":
    sys.exit(check())
