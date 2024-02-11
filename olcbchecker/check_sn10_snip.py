#!/usr/bin/env python3.10
'''
This uses a CAN link layer to check the SNIP protocol

Usage:
python3.10 check_sn10_snip.py

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

    import olcbchecker.setup
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
        if not PIP.SIMPLE_NODE_IDENTIFICATION_PROTOCOL in pipSet :
            if trace >= 10 : 
                print("Passed - due to SNIP not in PIP")
            return(0)
    
    # send an SNIP request message to provoke response
    message = Message(MTI.Simple_Node_Ident_Info_Request, NodeID(olcbchecker.ownnodeid()), destination)
    olcbchecker.sendMessage(message)

    results = []
    while True :
        try :
            received = olcbchecker.getMessage() # timeout if no entries
            # is this a snip reply?
            if not received.mti == MTI.Simple_Node_Ident_Info_Reply : continue # wait for next
        
            if destination != received.source : # check source in message header
                print ("Failure - Unexpected source of reply message: {} {}".format(received, received.source))
                return(3)
        
            if NodeID(olcbchecker.ownnodeid()) != received.destination : # check destination in message header
                print ("Failure - Unexpected destination of reply message: {} {}".format(received, received.destination))
                return(3)
        
            # accumulate the data
            results.extend(received.data)
        except Empty:
            break  # finished receiving the reply

    # now check the reply

    if not len(results) >=6 :
        print("Failure - only {} bytes received".format(len(results)))
        return(3)
    if not(results[0] ==1 or results[0] == 4) :
        print("Failure - unexpected value in 1st byte: 0x{:02X}".format(results[0]))
        return(3)
    # there should be exactly six zero bytes
    if results.count(0) != 6:
        print("Failure - unexpected number of zero bytes: {}".format(results.count(0)))
        return(3)

    zeroIndex = [i for i, n in enumerate(results) if n == 0]

    if not(results[zeroIndex[3]+1] ==1 or results[zeroIndex[3]+1] == 2) :
        print("Failure - unexpected value in 2nd version byte: 0x{:02X}".format(results[0]))
        return(3)

    if results[zeroIndex[3]+1] != 1 and results[zeroIndex[3]+1] != 2 :
        print("Failure - unexpected 2nd version number: {}".format(results[zeroIndex[3]+1]))
        return(3)
    
    if zeroIndex[0] > 41 :
        print ("Failure - first string too long: {}".format(zeroIndex[0] -1))
        return(3)
    
    if zeroIndex[1] - zeroIndex[0] > 41:
        print ("Failure - second string too long: {}".format(zeroIndex[1] - zeroIndex[0]))
        return(3)
    
    if zeroIndex[2] - zeroIndex[1] > 21:
        print ("Failure - third string too long: {}".format(zeroIndex[2] - zeroIndex[1]))
        return(3)
    
    if zeroIndex[3] - zeroIndex[2] > 21:
        print ("Failure - fourth string too long: {}".format(zeroIndex[3] - zeroIndex[2]))
        return(3)
    
    if zeroIndex[4] - zeroIndex[3] > 63:
        print ("Failure - fifth string too long: {}".format(zeroIndex[4] - zeroIndex[3]))
        return(3)
    
    if zeroIndex[5] - zeroIndex[4] > 64:
        print ("Failure - sixth string too long: {}".format(zeroIndex[5] - zeroIndex[4]))
        return(3)

    if zeroIndex[5] != len(results)-1:
        print ("Failure - data after the sixth zero byte")
        return(3)
    
    if trace >= 10 :
        #  print results
        print("Contents received:")
        display(1, zeroIndex[0], results)
        display(zeroIndex[0]+1, zeroIndex[1], results)
        display(zeroIndex[1]+1, zeroIndex[2], results)
        display(zeroIndex[2]+1, zeroIndex[3], results)
        display(zeroIndex[3]+2, zeroIndex[4], results)
        display(zeroIndex[4]+1, zeroIndex[5], results)
    
    if trace >= 10 : print("Passed")
    return 0

def display(startIndex, endIndex, results) :
    output = ""
    for letter in results[startIndex:endIndex] :
        output = output+chr(letter)
    print ("  ", output)
    
if __name__ == "__main__":
    sys.exit(check())
    
