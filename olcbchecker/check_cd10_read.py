#!/usr/bin/env python3.10
'''
This uses a CAN link layer to check CDI contents against schema

Usage:
python3.10 check_mc10_co.py

The -h option will display a full list of options.
'''

import sys

from openlcb.nodeid import NodeID
from openlcb.message import Message
from openlcb.mti import MTI
from openlcb.pip import PIP

import xmlschema

from queue import Empty

import olcbchecker.setup

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
            received = olcbchecker.getMessage() # timeout if no entries
            # is this a datagram reply, OK or not?
            if not (received.mti == MTI.Datagram_Received_OK or received.mti == MTI.Datagram_Rejected) : 
                continue # wait for next
    
            if destination != received.source : # check source in message header
                continue
    
            if NodeID(olcbchecker.ownnodeid()) != received.destination : # check destination in message header
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
            received = olcbchecker.getMessage() # timeout if no entries
            # is this a datagram reply, OK or not?
            if not (received.mti == MTI.Datagram) : 
                continue # wait for next
    
            if destination != received.source : # check source in message header
                continue
    
            if NodeID(olcbchecker.ownnodeid()) != received.destination : # check destination in message header
                continue

            # here we've received the reply datagram
            # send the reply
            message = Message(MTI.Datagram_Received_OK, NodeID(olcbchecker.ownnodeid()), destination, [0])
            olcbchecker.sendMessage(message)

            return received
            
        except Empty:
            raise Exception("Failure - no reply datagram received")
    
    


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
        if not PIP.CONFIGURATION_DESCRIPTION_INFORMATION in pipSet :
            if trace >= 10 : 
                print("Passed - due to CDI protocol not in PIP")
            return(0)

    address = 0
    LENGTH = 64
    content = []
    
    while not 0x00 in content : 
    
        ad1 = (address >> 24) & 0xFF
        ad2 = (address >> 16) & 0xFF
        ad3 = (address >> 8) & 0xFF
        ad4 = address & 0xFF
        
        # send an read datagran
        request = [0x20, 0x43, ad1,ad2,ad3,ad4, LENGTH]
        message = Message(MTI.Datagram, NodeID(olcbchecker.ownnodeid()), destination, request)
        olcbchecker.sendMessage(message)

        try :
            reply = getReplyDatagram(destination)
        except Exception as e:
            print (e)
            return (3)
        
        content.extend(reply.data[6:]) 
        address = address+LENGTH
         
    # here have CDI, perhaps plus a few zeros.
    # convert to string
    result = ""
    for one in content:  
        if one == 0 : break
        result = result+chr(one)
    
    # tempory write to file; this needs to be changed to in-memory
    temp = open("tempCDI.xml", "w")
    temp.write(result)
    temp.close()
    
    try :
        xmlschema.validate('tempCDI.xml', 'cdi.xsd')
    except Exception as e:
        print("Failure - CDI XML did not validate ", e)
        return 3
    
    if trace >= 10 : print("Passed")
    return 0

if __name__ == "__main__":
    sys.exit(check())
