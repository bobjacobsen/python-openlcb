#!/usr/bin/env python3.10
'''
This uses a CAN link layer to check response to an CID frame alias collision

Usage:
python3.10 check_fr20_ame.py

The -h option will display a full list of options.
'''

import sys

from openlcb.nodeid import NodeID
from openlcb.canbus.canframe import CanFrame
from openlcb.canbus.controlframe import ControlFrame
from queue import Empty

import olcbchecker.framelayer

def getFrame(timeout=0.3) :
    return olcbchecker.framelayer.readQueue.get(True, timeout)

def purgeFrames(timeout=0.3):
    while True :
        try :
            received = getFrame(timeout) # timeout if no entries
        except Empty:
             break

def check():
    # set up the infrastructure

    trace = olcbchecker.framelayer.trace # just to be shorter

    timeout = 0.3
    
    purgeFrames()

    ###############################
    # checking sequence starts here
    ###############################

    # send the AME frame to start the exchange
    ame = CanFrame(ControlFrame.AME.value, 0x001)  # bogus alias
    olcbchecker.framelayer.sendCanFrame(ame)
    
    try :
        # check for AMD frame from expected node (might be more than one AMD frame)
        while True: 
            reply1 = getFrame()
            if (reply1.header & 0xFF_FFF_000) != 0x10_701_000 :
                print ("Failure - frame was not AMD frame in first part")
                return 3
        
            # check it carries a node ID
            if len(reply1.data) < 6 :
                print ("Failure - first AMD frame did not carry node ID")
                return 3
        
            # and it's the right node ID
            targetnodeid = olcbchecker.framelayer.configure.targetnodeid
            if targetnodeid == None :
                # take first one we get 
                targetnodeid = str(NodeID(reply1.data))
                alias = reply1.header&0xFFF
                break  
            if NodeID(targetnodeid) != NodeID(reply1.data) :
                # but this wasn't the right one
                continue
                
            alias = reply1.header&0xFFF
            break
 
        purgeFrames()
        
        # Send a CID using that alias
        cid = CanFrame(ControlFrame.CID.value, alias, [])
        olcbchecker.framelayer.sendCanFrame(cid)

        # check for RID frame
        reply = getFrame()
        if (reply.header & 0xFF_FFF_000) != 0x10_700_000 :
            print ("Failure - frame was not RID frame in second part")
            return 3

        # collision in CID properly responded to, lets try an AMD collision
        amd = CanFrame(ControlFrame.AMD.value, alias, NodeID(targetnodeid).toArray())
        olcbchecker.framelayer.sendCanFrame(amd)

        # check for AMR frame
        reply = getFrame()
        if (reply.header & 0xFF_FFF_000) != 0x10_703_000 :
            print ("Failure - frame was not AMR frame in second part")
            return 3
        
        # check for _optional_ CID 7 frame with different alias
        try :
            replyCIDp = getFrame()
            if (replyCIDp.header & 0xFF_000_000) != 0x17_000_000 :
                print ("Failure - frame was not CID frame in second part")
                return 3
            # check for _different_ alias
            if (replyCIDp.header & 0x00_000_FFF) == alias :
                print ("Failure - did not receive different alias on CID")
                return 3

        except Empty : 
            # this is an OK case too
            pass
        
        
    except Empty:
        print ("Failure - did not receive expected frame")
        return 3

    if trace >= 10 : print("Passed")
    return 0
 
if __name__ == "__main__":
    sys.exit(check())
    
