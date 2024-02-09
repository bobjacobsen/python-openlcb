#!/usr/bin/env python3.10
'''
This uses a CAN link layer to check Identify Consumers messages

Usage:
python3.10 check_ev30_ic.py 

The -h option will display a full list of options.
'''

import sys

from openlcb.nodeid import NodeID
from openlcb.message import Message
from openlcb.mti import MTI
from openlcb.pip import PIP
from openlcb.eventid import EventID

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
        if not PIP.EVENT_EXCHANGE_PROTOCOL in pipSet :
            if trace >= 10 : 
                print("Passed - due to Event Exchange not in PIP")
            return(0)

    # send an Identify Events Addressed  message to accumulate producers to check
    message = Message(MTI.Identify_Events_Addressed , NodeID(conformance.ownnodeid()), destination)
    conformance.sendMessage(message)

    # does not include range replies
    consumerIdMTIs = [MTI.Consumer_Identified_Unknown, MTI.Consumer_Identified_Active, MTI.Consumer_Identified_Inactive]
    
    consumedEvents = set(())
    
    while True :
        try :
            received = conformance.getMessage() # timeout if no entries
            # is this a reply?
            if received.mti not in consumerIdMTIs :
                    continue # just skip
                
            if destination != received.source : # check source in message header
                print ("Failure - Unexpected source of reply message: {} {}".format(received, received.source))
                return(3)

            if received.mti in consumerIdMTIs :
                    consumedEvents.add(EventID(received.data))
        except Empty:
            # stopped getting messages, proceed
            break

    # have the set to check, proceed to check each one
    for event in consumedEvents :
        message = Message(MTI.Identify_Consumer, NodeID(conformance.ownnodeid()), None, event.toArray())
        conformance.sendMessage(message)

        try:
            while True : # in case we need to skip PCER messages
                received = conformance.getMessage() # timeout if no entries
                # is this a reply? Some nodes emit PCER after verify
                if received.mti not in consumerIdMTIs :
                    continue 
                # does the event ID match?
                if EventID(received.data) != event :
                    continue
                break

        except Empty:
            # no reply, error
            print ("Failure - No reply for event: {}".format(event))
            return (3)
        
    if trace >= 10 : print("Passed")
    return 0

if __name__ == "__main__":
    sys.exit(check())
