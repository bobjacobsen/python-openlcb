#!/usr/bin/env python3.10
'''
This uses a CAN link layer to check memmory configuration restart command

Usage:
python3.10 check_mc10_co.py

The -h option will display a full list of options.
'''

import sys

from openlcb.nodeid import NodeID
from openlcb.message import Message
from openlcb.mti import MTI
from openlcb.pip import PIP

from queue import Empty

import olcbchecker.setup


def check():
    # set up the infrastructure

    trace = olcbchecker.trace() # just to be shorter

    # pull any early received messages
    olcbchecker.purgeMessages()

    # get configured DUT node ID - this uses Verify Global in some cases, but not all
    destination = olcbchecker.getTargetID()

    ###############################
    # checking sequence starts here
    ###############################
    
    # check if PIP says this is present
    if olcbchecker.isCheckPip() : 
        pipSet = olcbchecker.gatherPIP(destination)
        if pipSet is None:
            print ("Failed in setup, no PIP information received")
            return (2)
        if not PIP.MEMORY_CONFIGURATION_PROTOCOL in pipSet :
            if trace >= 10 : 
                print("Passed - due to Memory Configuration protocol not in PIP")
            return(0)

    # send an datagram to restart the node
    message = Message(MTI.Datagram, NodeID(olcbchecker.ownnodeid()), destination, [0x20, 0xA9])
    olcbchecker.sendMessage(message)

    while True :
        try :
            received = olcbchecker.getMessage(20)  # might take a while to reboot
            # is this a reply from that node?
            if received.mti == MTI.Initialization_Complete or received.mti == MTI.Initialization_Complete_Simple :
                # this is an init message, passes
                break
        except Empty:
            print("Failure - did not receive Initialization Complete")
            return 3
            
    if trace >= 10 : print("Passed")
    return 0

if __name__ == "__main__":
    sys.exit(check())
