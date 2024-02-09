#!/usr/bin/env python3.10
'''
This uses a CAN link layer to check for initialization

Usage:
python3.10 check_me10_init.py

The -h option will display a full list of options.
'''

import sys

from openlcb.nodeid import NodeID
from openlcb.message import Message
from openlcb.mti import MTI
from openlcb.eventid import EventID

from queue import Empty

def check():
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
    
    #prompt operator to restart node
    print("Please reset/restart the DUT now")

    while True :
        try :
            received = olcbchecker.getMessage(15) # long reset timeout to wait for manual restart
            # is this a reply from that node?
            if received.mti == MTI.Initialization_Complete or received.mti == MTI.Initialization_Complete_Simple :
                # this is an init message, check source
                if destination != received.source : 
                    print("Failure - source address not correct")
                    return(3)
                # success
                break                
       
            print("Failure - received unexpected message type: {}".format(received))
        
        except Empty:
            print ("Failure - Did not receive Initialization Complete message")
            return(3)

    if trace >= 10 : print("Passed")
    return 0

if __name__ == "__main__":
    sys.exit(check())
