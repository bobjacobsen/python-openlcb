#!/usr/bin/env python3.10
'''
This uses a CAN link layer to test Identify Producers messages

Usage:
python3.10 check_ev30_ip.py 

The -h option will display a full list of options.
'''

import sys

from openlcb.nodeid import NodeID
from openlcb.message import Message
from openlcb.mti import MTI
from openlcb.pip import PIP
from openlcb.eventid import EventID

from queue import Empty

def test():
    # set up the infrastructure

    import conformance.setup
    trace = conformance.trace() # just to be shorter

    # pull any early received messages
    conformance.purgeMessages()

    # get configured DUT node ID - this uses Verify Global in some cases, but not all
    destination = conformance.getTargetID()

    ###########################
    # test sequence starts here
    ###########################

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

    # send an Identify Events Addressed  message to accumulate producers to test
    message = Message(MTI.Identify_Events_Addressed , NodeID(conformance.ownnodeid()), destination)
    conformance.sendMessage(message)

    # does not include range replies
    producerIdMTIs = [MTI.Producer_Identified_Unknown, MTI.Producer_Identified_Active, MTI.Producer_Identified_Inactive]
    
    producedEvents = set(())
    
    while True :
        try :
            received = conformance.getMessage() # timeout if no entries
            # is this a reply?
            if received.mti not in producerIdMTIs :
                    continue # just skip
                
            if destination != received.source : # check source in message header
                print ("Failure - Unexpected source of reply message: {} {}".format(received, received.source))
                return(3)

            if received.mti in producerIdMTIs :
                    producedEvents.add(EventID(received.data))
                    
        except Empty:
            # stopped getting messages, proceed
            break

    # have the set to check, proceed to check each one
    for event in producedEvents :
        message = Message(MTI.Identify_Producer, NodeID(conformance.ownnodeid()), None, event.toArray())
        conformance.sendMessage(message)

        try:
            while True : # in case we need to skip PCER messages
                received = conformance.getMessage() # timeout if no entries
                # is this a reply? Some nodes emit PCER after verify
                if received.mti not in producerIdMTIs :
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
    sys.exit(test())
