#!/usr/bin/env python3.10
'''
This uses a CAN link layer to check for an OIR reply to an unknown MTI

Usage:
python3.10 check_oir.py

The -h option will display a full list of options.
'''

import sys

from openlcb.nodeid import NodeID
from openlcb.message import Message
from openlcb.mti import MTI

from queue import Empty

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
    
# send a message with bogus MTI to provoke response
message = Message(MTI.New_Node_Seen, NodeID(conformance.ownnodeid()), destination) # MTI selected to be addressed
conformance.sendMessage(message)

while True :
    try :
        received = conformance.getMessage(timeout) # timeout if no entries
        # is this a reply from that node?
        if not received.mti == MTI.Optional_Interaction_Rejected : continue # wait for next
        # this is a OIR message, success
        # TODO - check the received data
        break
    except Empty:
        print ("Failure - Did not receive Optional Interaction Rejected reply")
        sys.exit(3)

if trace >= 10 : print("Passed")