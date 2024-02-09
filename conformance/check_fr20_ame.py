#!/usr/bin/env python3.10
'''
This uses a CAN link layer to check response to an AME frame

Usage:
python3.10 check_fr20_ame.py

The -h option will display a full list of options.
'''

import sys

from openlcb.nodeid import NodeID
from openlcb.canbus.canframe import CanFrame
from openlcb.canbus.controlframe import ControlFrame
from queue import Empty

import conformance.framelayer

def getFrame(timeout=0.3) :
    return conformance.framelayer.readQueue.get(True, timeout)

def purgeFrames(timeout=0.3):
    while True :
        try :
            received = getFrame(timeout) # timeout if no entries
        except Empty:
             break

def check():
    # set up the infrastructure

    trace = conformance.framelayer.trace # just to be shorter

    timeout = 0.3
    
    purgeFrames()

    ###############################
    # checking sequence starts here
    ###############################

    # send the AME frame to start the exchange
    frame = CanFrame(ControlFrame.AME.value, 0x001)  # bogus alias
    conformance.framelayer.canPhysicalLayerGridConnect.sendCanFrame(frame)
    
    try :
        # check for AMD frame
        frame = getFrame(1.0)
        if (frame.header & 0xFF_FFF_000) != 0x10_701_000 :
            print ("Failure - frame was not AMD frame in first part")
            return 3
        
        # check it carries a node ID
        if len(frame.data) < 6 :
            print ("Failure - first AMD frame did not carry node ID")
            return 3
        
        purgeFrames()
        
        # get that node ID, create and send an AMD using it
        frame = CanFrame(ControlFrame.AME.value, 0x001, frame.data)  # bogus alias
        conformance.framelayer.canPhysicalLayerGridConnect.sendCanFrame(frame)

        # check for AMD frame
        frame = getFrame(1.0)
        if (frame.header & 0xFF_FFF_000) != 0x10_701_000 :
            print ("Failure - frame was not AMD frame in second part")
            return 3
        
        # check it carries a node ID
        if len(frame.data) < 6 :
            print ("Failure - second AMD frame did not carry node ID")
            return 3
        
        
    except Empty:
        print ("Failure - did not receive expected frame")
        return 3

    if trace >= 10 : print("Passed")
    return 0
 
if __name__ == "__main__":
    sys.exit(check())
    
