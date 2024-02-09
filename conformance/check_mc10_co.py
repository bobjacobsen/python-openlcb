#!/usr/bin/env python3.10
'''
This uses a CAN link layer to check memmory configuration options command

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

import conformance.setup

def getReplyDatagram(destination) :
    '''
    Invoked after a datagram has been sent, this waits
    for first the datagram reply message, then a 
    datagram message that contains a reply.  It 
    replies with a datagram OK, then returns the reply datagram message.
    Raises Exception if something went wrong.
    '''
    # first, wait for the reply
    while True :
        try :
            received = conformance.getMessage() # timeout if no entries
            # is this a datagram reply, OK or not?
            if not (received.mti == MTI.Datagram_Received_OK or received.mti == MTI.Datagram_Rejected) : 
                continue # wait for next
    
            if destination != received.source : # check source in message header
                continue
    
            if NodeID(conformance.ownnodeid()) != received.destination : # check destination in message header
                continue
    
            if received.mti == MTI.Datagram_Received_OK :
                # OK, proceed
                break
            else : # must be datagram rejected
                # can't proceed
                raise Exception("Failure - Original Datagram rejected")

        except Empty:
            raise Exception("Failure - no reply to original request")
    
    # now wait for the reply datagram
    while True :
        try :
            received = conformance.getMessage() # timeout if no entries
            # is this a datagram reply, OK or not?
            if not (received.mti == MTI.Datagram) : 
                continue # wait for next
    
            if destination != received.source : # check source in message header
                continue
    
            if NodeID(conformance.ownnodeid()) != received.destination : # check destination in message header
                continue

            # here we've received the reply datagram
            # send the reply
            message = Message(MTI.Datagram_Received_OK, NodeID(conformance.ownnodeid()), destination, [0])
            conformance.sendMessage(message)

            return received
            
        except Empty:
            raise Exception("Failure - no reply datagram received")
    
    


def check():
    # set up the infrastructure

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
        if not PIP.MEMORY_CONFIGURATION_PROTOCOL in pipSet :
            if trace >= 10 : 
                print("Passed - due to Memory Configuration protocol not in PIP")
            return(0)

    # send an datagram to provoke response
    message = Message(MTI.Datagram, NodeID(conformance.ownnodeid()), destination, [0x20, 0x80])
    conformance.sendMessage(message)

    try :
        reply = getReplyDatagram(destination)
    except Exception as e:
        print (e)
        return (3)
        
    # check that the reply is OK
    if len(reply.data) < 6 :
        print ("Failure - reply was too short")
        return (3)
        
    if reply.data[3] != 0 or (reply.data[2]&0x01) != 0 :
        print ("Failure - improper command bits set")
        return (3)
    
    if (reply.data[4]&0x0C) != 0 :
        print ("Failure - improper write bits set")
        return (3)
    
    if trace >= 10 : print("Passed")
    return 0

if __name__ == "__main__":
    sys.exit(check())
